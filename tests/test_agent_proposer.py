from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import mosaic.agent_proposer as proposer
from mosaic.agent_proposer import propose_and_verify, request_proposal, verify_proposal
from mosaic.final_cli import main
from mosaic.scenario_registry import get_scenario
from mosaic.web.complete_app import create_app


def _transport_for(proposal):
    def transport(endpoint, payload, timeout):
        assert endpoint == "http://model.test/api/generate"
        assert payload["stream"] is False
        assert payload["format"]["additionalProperties"] is False
        assert timeout == 7
        return {
            "model": "test-model",
            "done": True,
            "response": json.dumps(proposal),
            "prompt_eval_count": 10,
            "eval_count": 5,
        }

    return transport


def _valid_proposal():
    return {
        "selected_scenario": "research",
        "nominated_columns": ["zip5", "birth_date", "gender_category"],
        "rationale": "Three independently sourced semantic families converge in this export.",
        "pr_narrative": "Review a privacy-safe remediation for the lineage-derived research export.",
    }


def test_agent_can_propose_but_only_policy_accepts_for_human_review() -> None:
    report = propose_and_verify(
        "research",
        endpoint="http://model.test/api/generate",
        model="test-model",
        timeout=7,
        transport=_transport_for(_valid_proposal()),
    )
    assert report["status"] == "accepted_for_human_review"
    assert report["model_role"] == "proposal_only"
    assert report["policy_role"] == "deterministic_verdict_and_veto"
    verification = report["verification"]
    assert verification["policy_veto"] is False
    assert verification["deterministic_assessment"]["assessment"]["verdict"] == "validated_critical"
    assert verification["raw_person_rows_returned"] == 0
    assert verification["compiled_aggregate_query"].startswith("SELECT zip5")
    assert verification["generated_code_executed"] is False
    assert verification["mutation_performed"] is False


def test_policy_vetoes_row_level_or_under_supported_model_proposal() -> None:
    proposal = _valid_proposal()
    proposal["nominated_columns"] = ["zip5"]
    result = verify_proposal(proposal, [get_scenario("research")])
    assert result["status"] == "vetoed"
    assert result["policy_veto"] is True
    assert any("at least two" in reason for reason in result["veto_reasons"])
    assert result["generated_code_executed"] is False


def test_agent_cannot_select_an_asset_outside_supplied_context() -> None:
    proposal = _valid_proposal()
    proposal["selected_scenario"] = "invented"
    result = verify_proposal(proposal, [get_scenario("research")])
    assert result["status"] == "vetoed"
    assert "outside the allowlisted DataHub context" in result["veto_reasons"][0]
    assert result["deterministic_assessment"] is None


def test_cli_reports_external_model_failure_honestly(monkeypatch, capsys) -> None:
    monkeypatch.setenv("MOSAIC_AGENT_ENDPOINT", "not-a-url")
    assert main(["assess", "--agent", "--scenario", "research"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "blocked_external_model"
    assert result["policy_veto"] is True


def test_recorded_agent_receipts_are_publicly_inspectable() -> None:
    response = TestClient(create_app(Path.cwd())).get("/api/agent-receipts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["execution_boundary"].startswith("recorded local Ollama")
    statuses = {receipt["status"] for receipt in payload["receipts"]}
    assert statuses == {"accepted_for_human_review", "vetoed"}
    accepted = next(item for item in payload["receipts"] if item["status"].startswith("accepted"))
    assert accepted["verification"]["generated_code_executed"] is False
    assert accepted["verification"]["mutation_performed"] is False


class _Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.body


def test_ollama_transport_validates_endpoint_and_network_response(monkeypatch) -> None:
    body = json.dumps({"response": "{}", "done": True}).encode()
    monkeypatch.setattr(
        proposer.urllib.request, "urlopen", lambda *_args, **_kwargs: _Response(body)
    )
    result = proposer._ollama_transport("http://localhost/api/generate", {"model": "x"}, 1)
    assert result["done"] is True
    with pytest.raises(ValueError, match="absolute HTTP"):
        proposer._ollama_transport("file:///tmp/model", {}, 1)

    def unavailable(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(proposer.urllib.request, "urlopen", unavailable)
    with pytest.raises(RuntimeError, match="model unavailable"):
        proposer._ollama_transport("http://localhost/api/generate", {}, 1)


def test_request_proposal_rejects_missing_and_malformed_structured_output() -> None:
    spec = [get_scenario("research")]

    def missing(*_args):
        return {"done": True}

    def malformed(*_args):
        return {"response": "not-json"}

    with pytest.raises(RuntimeError, match="no structured response"):
        request_proposal(spec, endpoint="http://model", model="x", transport=missing)
    with pytest.raises(RuntimeError, match="malformed structured output"):
        request_proposal(spec, endpoint="http://model", model="x", transport=malformed)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            {"selected_scenario": "control", "nominated_columns": ["job_execution_id", "x"]},
            "negative control",
        ),
        ({"nominated_columns": ["zip5", 1]}, "string quasi-identifier"),
        ({"nominated_columns": ["zip5", "zip5"]}, "unique members"),
        ({"nominated_columns": ["zip5", "unknown"]}, "unique members"),
        ({"nominated_columns": ["zip5", "billing_zipcode"]}, "unique members"),
        ({"rationale": "short"}, "substantive"),
        ({"pr_narrative": None}, "substantive"),
    ],
)
def test_verifier_fail_closed_branches(change, reason) -> None:
    proposal = _valid_proposal()
    proposal.update(change)
    allowed = (
        [get_scenario("control")]
        if proposal["selected_scenario"] == "control"
        else [get_scenario("research")]
    )
    result = verify_proposal(proposal, allowed)
    assert result["policy_veto"] is True
    assert any(reason in item for item in result["veto_reasons"])
    assert result["compiled_aggregate_query"] is None


def test_agent_receipt_api_fails_closed_when_missing_or_malformed(tmp_path: Path) -> None:
    assert TestClient(create_app(tmp_path)).get("/api/agent-receipts").status_code == 404
    root = tmp_path / "evidence" / "external"
    root.mkdir(parents=True)
    (root / "ollama-agent-accepted-live.json").write_text("not-json", encoding="utf-8")
    assert TestClient(create_app(tmp_path)).get("/api/agent-receipts").status_code == 503


def test_agent_cli_returns_deterministic_assessment_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        proposer,
        "propose_and_verify",
        lambda *_args, **_kwargs: {
            "status": "accepted_for_human_review",
            "verification": {"deterministic_assessment": {"exit_code": 0}},
        },
    )
    assert main(["assess", "--agent", "--scenario", "research"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "accepted_for_human_review"
