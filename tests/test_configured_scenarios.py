from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from mosaic.estate_scan import scan_estate
from mosaic.final_cli import main
from mosaic.scenario_registry import assess_scenario, get_scenario, list_scenarios
from mosaic.web.complete_app import create_app


@pytest.mark.parametrize(
    ("slug", "verdict", "minimum_k", "below_5", "query_expected"),
    [
        ("research", "validated_critical", 1, 100.0, True),
        ("mitigated", "validated_low", 20, 0.0, True),
        ("control", "screening_only", None, None, False),
        ("audience", "validated_critical", 1, 100.0, True),
    ],
)
def test_configured_scenarios_are_independent_backend_assessments(
    slug, verdict, minimum_k, below_5, query_expected
) -> None:
    report = assess_scenario(slug)
    assessment = report["assessment"]
    assert assessment["verdict"] == verdict
    assert assessment["raw_rows_returned"] == 0
    assert bool(assessment["aggregate_query"]) is query_expected
    if minimum_k is None:
        assert assessment["metrics"] is None
    else:
        assert assessment["metrics"]["minimum_k"] == minimum_k
        assert assessment["metrics"]["percent_below_5"] == below_5
    assert len(report["scenario"]["configuration_sha256"]) == 64
    assert report["writeback"]["mutation_performed"] is False


def test_scenario_library_is_stable_and_configuration_driven() -> None:
    scenarios = list_scenarios()
    assert [item.slug for item in scenarios] == ["audience", "control", "mitigated", "research"]
    assert len({item.config_sha256 for item in scenarios}) == len(scenarios)
    assert all(item.asset_urn.startswith("urn:li:dataset:") for item in scenarios)


@pytest.mark.parametrize("slug", ["", "missing", "../research", "RESEARCH", "research.json"])
def test_scenario_lookup_fails_closed(slug: str) -> None:
    with pytest.raises(KeyError):
        get_scenario(slug)


def test_estate_scan_ranks_critical_findings_first_without_raw_rows() -> None:
    report = scan_estate()
    findings = report["ranked_findings"]
    assert report["status"] == "passed"
    assert report["assets_screened"] == 4
    assert report["critical_findings"] == 2
    assert report["raw_rows_returned"] == 0
    assert [item["severity"] for item in findings] == sorted(
        [item["severity"] for item in findings], reverse=True
    )
    assert {item["scenario"] for item in findings[:2]} == {"research", "audience"}
    assert findings[-1]["scenario"] == "mitigated"


def test_scenario_and_scan_apis_are_judge_inspectable(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    listing = client.get("/api/scenarios")
    assert listing.status_code == 200
    assert len(listing.json()["scenarios"]) == 4
    assert client.get("/api/scenarios/research").json()["assessment"]["metrics"]["minimum_k"] == 1
    assert client.get("/api/scenarios/control").json()["assessment"]["metrics"] is None
    assert client.get("/api/scenarios/missing").status_code == 404
    assert client.get("/api/scan").json()["assets_screened"] == 4


@pytest.mark.parametrize(
    ("slug", "expected_code"),
    [("research", 3), ("audience", 3), ("mitigated", 0), ("control", 0)],
)
def test_assess_cli_supports_every_configured_scenario(slug, expected_code, capsys) -> None:
    assert main(["assess", "--scenario", slug]) == expected_code
    assert json.loads(capsys.readouterr().out)["scenario"]["slug"] == slug


def test_assess_cli_writes_portable_evidence(tmp_path, capsys) -> None:
    output = tmp_path / "nested" / "assessment.json"
    assert main(["assess", "--scenario", "mitigated", "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(capsys.readouterr().out)


def test_scan_cli_returns_critical_gate_and_output(tmp_path, capsys) -> None:
    output = tmp_path / "scan.json"
    assert main(["scan", "--output", str(output)]) == 3
    report = json.loads(capsys.readouterr().out)
    assert report["critical_findings"] == 2
    assert json.loads(output.read_text(encoding="utf-8")) == report


def test_assess_cli_rejects_unknown_scenario() -> None:
    with pytest.raises(SystemExit, match="2"):
        main(["assess", "--scenario", "unknown"])
