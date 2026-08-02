from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _module():
    path = Path("scripts/final_submission_audit.py")
    spec = importlib.util.spec_from_file_location("final_submission_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _clean_git(*args: str) -> str:
    if args == ("status", "--porcelain"):
        return ""
    if args == ("remote", "get-url", "origin"):
        return "https://github.com/usv240/mosaic-datahub.git"
    return "a" * 40


def test_offline_submission_audit_proves_every_local_receipt(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "_git", _clean_git)
    checks = module.audit(allow_pending_video=True)
    assert checks
    assert all(check.passed for check in checks)
    video = next(check for check in checks if check.name.startswith("public video"))
    assert video.name == "public video (preview bypass)"
    assert video.detail.startswith("BYPASSED:")


def test_strict_submission_audit_refuses_missing_public_video(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "_git", _clean_git)
    checks = module.audit()
    failures = {check.name for check in checks if not check.passed}
    assert failures == {"public video"}
    video = next(check for check in checks if check.name == "public video")
    assert video.detail.startswith("PENDING:")


def test_deployment_endpoint_exposes_revision(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from mosaic.web import create_app

    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc123")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")
    assert TestClient(create_app()).get("/api/deployment").json() == {
        "status": "ok",
        "commit_sha": "abc123",
        "environment": "production",
    }
