from fastapi.testclient import TestClient

from mosaic.web.complete_app import create_app


def test_public_demo_refuses_runtime_evidence_writes(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MOSAIC_PUBLIC_DEMO", "true")
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/runs")
    assert response.status_code == 403
    assert "read-only" in response.json()["detail"]
    assert not (tmp_path / "runs").exists()
