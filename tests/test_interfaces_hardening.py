from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import mosaic.engine as engine
from mosaic.controls import run_safe_controls
from mosaic.final_cli import main
from mosaic.mitigation import simulate_birth_date_suppression
from mosaic.mitigation_lab import compare_mitigations
from mosaic.models import Assessment, Candidate, RiskMetrics, Verdict
from mosaic.scenario import build_synthetic_estate
from mosaic.web.complete_app import create_app
from mosaic.writeback import (
    ApprovalRequiredError,
    InMemoryCatalog,
    build_proposal,
    publish_proposal,
)


@pytest.mark.parametrize(
    ("argv", "expected_host", "expected_port"),
    [
        (["serve"], "127.0.0.1", 8123),
        (["serve", "--host", "0.0.0.0"], "0.0.0.0", 8123),
        (["serve", "--port", "9000"], "127.0.0.1", 9000),
        (["serve", "--host", "localhost", "--port", "7777"], "localhost", 7777),
    ],
)
def test_cli_serve_contract(monkeypatch, argv, expected_host, expected_port) -> None:
    import uvicorn

    captured = {}
    monkeypatch.setattr(
        uvicorn, "run", lambda target, **kwargs: captured.update(target=target, **kwargs)
    )
    assert main(argv) == 0
    assert captured == {
        "target": "mosaic.web.complete_app:create_app",
        "host": expected_host,
        "port": expected_port,
        "factory": True,
    }


@pytest.mark.parametrize("status,expected", [("passed", 0), ("failed", 2), ("partial", 2)])
def test_cli_live_demo_status_and_output(monkeypatch, tmp_path, capsys, status, expected) -> None:
    import mosaic.complete_e2e

    captured = {}

    def fake_run(server, *, approve_writeback):
        captured.update(server=server, approved=approve_writeback)
        return {"status": status, "proof": True}

    monkeypatch.setattr(mosaic.complete_e2e, "run", fake_run)
    output = tmp_path / "nested" / "live.json"
    code = main(
        ["live-demo", "--server", "http://core", "--approve-writeback", "--output", str(output)]
    )
    assert code == expected
    assert captured == {"server": "http://core", "approved": True}
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == status
    assert json.loads(capsys.readouterr().out)["proof"] is True


@pytest.mark.parametrize("status,expected", [("passed", 0), ("failed", 2), ("unknown", 2)])
def test_cli_mcp_status_contract(monkeypatch, capsys, status, expected) -> None:
    import mosaic.mcp_probe

    captured = {}

    async def fake_probe(mcp_url, server):
        captured.update(mcp_url=mcp_url, server=server)
        return {"status": status}

    monkeypatch.setattr(mosaic.mcp_probe, "run_probe", fake_probe)
    code = main(["verify-mcp", "--mcp-url", "http://mcp", "--server", "http://core"])
    assert code == expected
    assert captured == {"mcp_url": "http://mcp", "server": "http://core"}
    assert json.loads(capsys.readouterr().out)["status"] == status


@pytest.mark.parametrize("flag", [[], ["--json"]])
def test_cli_demo_emits_complete_json(flag, capsys) -> None:
    assert main(["demo", *flag]) == 3
    report = json.loads(capsys.readouterr().out)
    assert report["product"] == "Mosaic"
    assert report["assessment"]["raw_rows_returned"] == 0
    assert report["mitigation_lab"]["recommended"]["meets_demo_policy"] is True


def test_cli_demo_creates_parent_and_output(monkeypatch, tmp_path, capsys) -> None:
    output = tmp_path / "evidence" / "report.json"
    assert main(["demo", "--output", str(output)]) == 3
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(capsys.readouterr().out)


@pytest.mark.parametrize(
    "argv",
    [[], ["unknown"], ["serve", "--port", "not-a-number"], ["demo", "--unknown"]],
)
def test_cli_fails_closed_on_invalid_arguments(argv) -> None:
    with pytest.raises(SystemExit, match="2"):
        main(argv)


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YeS"])
def test_public_demo_write_variants_are_blocked(monkeypatch, tmp_path, value) -> None:
    monkeypatch.setenv("MOSAIC_PUBLIC_DEMO", value)
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/runs")
    assert response.status_code == 403
    assert "read-only" in response.json()["detail"]
    assert list(tmp_path.rglob("*.json")) == []


@pytest.mark.parametrize("value", ["", "0", "false", "no", "disabled"])
def test_non_public_modes_allow_local_evidence(monkeypatch, tmp_path, value) -> None:
    monkeypatch.setenv("MOSAIC_PUBLIC_DEMO", value)
    response = TestClient(create_app(tmp_path)).post("/api/runs")
    assert response.status_code == 200
    assert response.json()["sha256"]


@pytest.mark.parametrize(
    "run_id",
    [
        "missing",
        "mosaic-missing",
        "../secret",
        "mosaic-../secret",
        "mosaic-..\\secret",
        "mosaic-/secret",
        "mosaic-\\secret",
        "MOSAIC-123",
        "",
    ],
)
def test_evidence_download_rejects_invalid_or_missing_ids(tmp_path, run_id) -> None:
    response = TestClient(create_app(tmp_path)).get(f"/api/runs/{run_id}/evidence.json")
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "expected"),
    [
        ("get", "/health", 200),
        ("post", "/health", 405),
        ("get", "/api/assessment", 200),
        ("post", "/api/assessment", 405),
        ("get", "/api/mitigations", 200),
        ("post", "/api/mitigations", 405),
        ("get", "/api/runs", 200),
        ("delete", "/api/runs", 405),
        ("get", "/", 200),
        ("get", "/runs", 200),
        ("get", "/not-found", 404),
    ],
)
def test_web_route_and_method_contract(tmp_path, method, path, expected) -> None:
    response = getattr(TestClient(create_app(tmp_path)), method)(path)
    assert response.status_code == expected


def test_web_history_is_newest_first_and_downloads_exact_bundle(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    first = client.post("/api/runs").json()
    second = client.post("/api/runs").json()
    history = client.get("/api/runs").json()["runs"]
    assert [item["run_id"] for item in history] == [second["run_id"], first["run_id"]]
    downloaded = client.get(f"/api/runs/{first['run_id']}/evidence.json")
    assert downloaded.json() == first
    assert "attachment" in downloaded.headers["content-disposition"]


def _assessment(metrics: RiskMetrics | None, verdict=Verdict.VALIDATED_CRITICAL) -> Assessment:
    candidate = Candidate(
        "urn:asset", ("zip5",), ("location",), (("source",),), True, ("downstream",)
    )
    return Assessment(candidate, verdict, ("reason",), metrics, "SELECT aggregate", 0)


@pytest.mark.parametrize("verdict", list(Verdict))
def test_writeback_proposal_maps_every_verdict(verdict) -> None:
    proposal = build_proposal(_assessment(RiskMetrics(10, 2, 5, 0, 0, 100, {5: 2}), verdict))
    assert proposal["properties"]["mosaic.riskState"] == verdict.value
    assert proposal["properties"]["mosaic.minimumK"] == 5
    assert proposal["document"]["raw_rows_returned"] == 0
    assert proposal["requires_reviewer_approval"] is True


def test_writeback_proposal_requires_exact_metrics() -> None:
    with pytest.raises(ValueError, match="exact metrics"):
        build_proposal(_assessment(None))


@pytest.mark.parametrize("approved", [False, None, 0, ""])
def test_writeback_rejects_all_falsy_approval_values(approved) -> None:
    with pytest.raises(ApprovalRequiredError):
        publish_proposal(InMemoryCatalog(), {"asset_urn": "urn:asset"}, approved=approved)


def test_writeback_reread_detects_catalog_mismatch() -> None:
    class MismatchCatalog(InMemoryCatalog):
        def read(self, urn):
            return {"different": urn}

    result = publish_proposal(MismatchCatalog(), {"asset_urn": "urn:asset"}, approved=True)
    assert result == {"status": "published", "reread_verified": False, "target_urn": "urn:asset"}


def test_engine_fails_if_lineage_discovery_returns_no_candidate(monkeypatch) -> None:
    monkeypatch.setattr(engine, "discover_convergences", lambda _estate: [])
    with pytest.raises(RuntimeError, match="lineage convergence"):
        engine.assess_demo()


def test_engine_validates_query_before_risk_computation(monkeypatch) -> None:
    monkeypatch.setattr(
        engine,
        "validate_aggregate_query",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("blocked")),
    )
    with pytest.raises(RuntimeError, match="blocked"):
        engine.assess_demo()


def test_judge_report_contract_is_deterministic() -> None:
    first = engine.run_judge_demo()
    second = engine.run_judge_demo()
    assert first == second
    assert first["synthetic_data_only"] is True
    assert first["exit_code"] == first["assessment"]["exit_code"] == 3
    assert first["writeback"]["status"] == "dry_run"


def test_controls_cover_expected_negative_cases() -> None:
    report = run_safe_controls(build_synthetic_estate())
    assert report["status"] == "passed"
    assert {control["name"] for control in report["controls"]} == {
        "generalized_export",
        "tagged_direct_identifier",
        "operational_identifier",
        "aggregate_dashboard",
    }
    assert all(control["actual"] == control["expected"] for control in report["controls"])


def test_suppression_is_shadow_only_and_measurably_safe() -> None:
    result = simulate_birth_date_suppression(build_synthetic_estate().rows)
    assert result["status"] == "recommended"
    assert result["writes_applied"] is False
    assert result["metrics"]["minimum_k"] >= 5
    assert "birth_date" not in result["evaluated_columns"]


def test_mitigation_lab_recommends_highest_utility_eligible_strategy() -> None:
    report = compare_mitigations()
    eligible = [item for item in report["strategies"] if item["meets_demo_policy"]]
    assert report["recommended"] == max(eligible, key=lambda item: item["utility_retained"])
    assert all(item["writes_applied"] is False for item in report["strategies"])
    assert report["baseline"]["minimum_k"] < report["recommended"]["minimum_k"]
