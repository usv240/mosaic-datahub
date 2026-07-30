from __future__ import annotations

import json

from fastapi.testclient import TestClient

from mosaic.runs import load_run, record
from mosaic.scenario_registry import assess_scenario
from mosaic.web.complete_app import create_app


def test_load_run_verifies_digest(tmp_path) -> None:
    saved = record(assess_scenario("research"), tmp_path)
    loaded = load_run(tmp_path, saved["run_id"])
    assert loaded["integrity"]["status"] == "verified"


def test_load_run_detects_tampering(tmp_path) -> None:
    saved = record(assess_scenario("research"), tmp_path)
    path = tmp_path / f"{saved['run_id']}.json"
    payload = json.loads(path.read_text())
    payload["assessment"]["verdict"] = "validated_low"
    path.write_text(json.dumps(payload))
    assert load_run(tmp_path, saved["run_id"])["integrity"]["status"] == "failed"


def test_scenario_run_has_detail_page_and_api(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    saved = client.post("/api/runs?scenario=mitigated").json()
    assert saved["scenario"]["slug"] == "mitigated"
    assert client.get(f"/api/runs/{saved['run_id']}").json()["integrity"]["status"] == "verified"
    page = client.get(f"/runs/{saved['run_id']}")
    assert page.status_code == 200
    assert "Print / save PDF" in page.text


def test_unknown_scenario_and_run_are_404(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.post("/api/runs?scenario=missing").status_code == 404
    assert client.get("/api/runs/mosaic-missing").status_code == 404
    assert client.get("/runs/mosaic-missing").status_code == 404
