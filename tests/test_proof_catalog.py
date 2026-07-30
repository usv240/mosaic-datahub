from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mosaic.proof_catalog import proof_catalog
from mosaic.web.complete_app import create_app


def test_proof_catalog_unifies_all_three_tiers() -> None:
    report = proof_catalog(Path.cwd())
    assert report["status"] == "passed"
    assert [proof["id"] for proof in report["proofs"]] == [
        "regression",
        "datahub-replay",
        "external-data",
    ]
    assert report["proofs"][2]["metrics"]["raw_rows_committed"] == 0
    assert report["contribution"]["status"] == "merged"


def test_proofs_api_is_judge_inspectable(tmp_path) -> None:
    client = TestClient(create_app(Path.cwd()))
    response = client.get("/api/proofs")
    assert response.status_code == 200
    assert response.json()["status"] == "passed"
