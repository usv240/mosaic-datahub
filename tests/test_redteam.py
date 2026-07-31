from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mosaic.final_cli import main
from mosaic.redteam import run_redteam
from mosaic.web.complete_app import create_app


def test_redteam_replays_metadata_injection_and_records_refusal() -> None:
    report = run_redteam()
    assert report["status"] == "passed"
    controls = report["controls"]
    assert controls["free_form_description_in_agent_allowlist"] is False
    assert controls["policy_refused_requested_sql"] is True
    assert controls["requested_sql_executed"] is False
    assert controls["run_continued_with_policy_compiled_aggregate"] is True
    assert controls["raw_person_rows_returned"] == 0
    assert "COUNT(*)" in controls["compiled_aggregate_query"]


def test_redteam_fails_if_policy_does_not_refuse() -> None:
    def unsafe_validator(_query: str, _asset: str, _columns: tuple[str, ...]) -> None:
        return None

    report = run_redteam(validator=unsafe_validator)
    assert report["status"] == "failed"
    assert report["controls"]["policy_refused_requested_sql"] is False
    assert report["failure_condition"]


def test_redteam_cli_is_a_reproducible_acceptance_gate(capsys) -> None:
    assert main(["redteam"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["attack"]["id"] == "datahub-description-prompt-injection"
    assert report["controls"]["mutation_performed"] is False


def test_redteam_rejects_malformed_transcript(tmp_path) -> None:
    malformed = tmp_path / "attack.json"
    malformed.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        run_redteam(malformed)


def test_redteam_receipt_is_visible_to_hosted_judges() -> None:
    response = TestClient(create_app(Path.cwd())).get("/api/redteam")
    assert response.status_code == 200
    assert response.json()["controls"]["policy_refused_requested_sql"] is True


def test_redteam_api_fails_closed_without_transcript(tmp_path) -> None:
    response = TestClient(create_app(tmp_path)).get("/api/redteam")
    assert response.status_code == 503


def test_redteam_rejects_unsupported_schema(tmp_path) -> None:
    transcript = json.loads(Path("fixtures/agent_transcripts/prompt-injection.json").read_text())
    transcript["schema_version"] = 2
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(transcript), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        run_redteam(path)


@pytest.mark.parametrize(
    ("proposal", "message"),
    [
        ("not-an-object", "must be an object"),
        ({"requested_sql": ""}, "must contain requested_sql"),
    ],
)
def test_redteam_rejects_invalid_adversarial_proposal(tmp_path, proposal, message) -> None:
    transcript = json.loads(Path("fixtures/agent_transcripts/prompt-injection.json").read_text())
    transcript["adversarial_proposal"] = proposal
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps(transcript), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        run_redteam(path)


def test_redteam_cli_writes_failed_receipt_for_bad_transcript(tmp_path, capsys) -> None:
    transcript = tmp_path / "bad.json"
    output = tmp_path / "receipt.json"
    transcript.write_text("{}", encoding="utf-8")
    assert main(["redteam", "--transcript", str(transcript), "--output", str(output)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    assert json.loads(output.read_text(encoding="utf-8"))["raw_person_rows_returned"] == 0
