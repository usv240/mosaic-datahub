from __future__ import annotations

from fastapi.testclient import TestClient

import mosaic.web.complete_app as web


def test_settings_explains_approval_model(tmp_path) -> None:
    page = TestClient(web.create_app(tmp_path)).get("/settings")
    assert page.status_code == 200
    assert "Publish synthetic evidence" in page.text
    assert "PUBLISH SYNTHETIC EVIDENCE" in page.text


def test_datahub_health_is_non_mutating_by_default(tmp_path) -> None:
    report = TestClient(web.create_app(tmp_path)).get("/api/health/datahub").json()
    assert report["status"] == "not_probed"
    assert report["web_writeback_enabled"] is False


def test_browser_publish_is_disabled_by_default(tmp_path) -> None:
    client = TestClient(web.create_app(tmp_path))
    assert client.get("/api/approval-token").status_code == 403
    assert (
        client.post("/api/publish", json={"csrf_token": "x", "confirmation": "x"}).status_code
        == 403
    )


def test_browser_publish_requires_token_and_exact_phrase(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MOSAIC_ENABLE_WEB_WRITEBACK", "true")
    captured = {}
    monkeypatch.setattr(
        web,
        "publish",
        lambda server, *, approved: (
            captured.update(server=server, approved=approved) or {"status": "published"}
        ),
    )
    client = TestClient(web.create_app(tmp_path))
    token = client.get("/api/approval-token").json()["csrf_token"]
    assert (
        client.post(
            "/api/publish",
            json={"csrf_token": "wrong", "confirmation": "PUBLISH SYNTHETIC EVIDENCE"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/publish", json={"csrf_token": token, "confirmation": "publish"}
        ).status_code
        == 400
    )
    result = client.post(
        "/api/publish", json={"csrf_token": token, "confirmation": "PUBLISH SYNTHETIC EVIDENCE"}
    )
    assert result.json()["status"] == "published"
    assert captured == {"server": "http://localhost:8080", "approved": True}


def test_public_demo_overrides_writeback_opt_in(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MOSAIC_ENABLE_WEB_WRITEBACK", "true")
    monkeypatch.setenv("MOSAIC_PUBLIC_DEMO", "true")
    client = TestClient(web.create_app(tmp_path))
    assert client.get("/api/approval-token").status_code == 403
    assert client.get("/api/health/datahub").json()["web_writeback_enabled"] is False
