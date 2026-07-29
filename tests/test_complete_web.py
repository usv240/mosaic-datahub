from fastapi.testclient import TestClient

from mosaic.web.complete_app import create_app


def test_complete_console_exposes_mitigations_and_history(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/health").json() == {"status": "ok"}
    mitigation = client.get("/api/mitigations").json()
    assert mitigation["recommended"]["meets_demo_policy"] is True
    saved = client.post("/api/runs").json()
    assert client.get("/api/runs").json()["runs"][0]["run_id"] == saved["run_id"]
    download = client.get(f"/api/runs/{saved['run_id']}/evidence.json")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/json"
    assert client.get("/api/runs/..%2Fsecret/evidence.json").status_code == 404
