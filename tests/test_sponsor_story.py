from pathlib import Path

from fastapi.testclient import TestClient

from mosaic.technology import technology_catalog
from mosaic.web.complete_app import create_app


def test_technology_catalog_maps_every_datahub_claim_to_proof() -> None:
    catalog = technology_catalog()
    assert catalog["sponsor"]["name"] == "DataHub"
    assert catalog["sponsor"]["technology"] == "Open-source Context Platform"
    assert len(catalog["workflow"]) == 5
    assert len(catalog["datahub_capabilities"]) == 7
    assert len(catalog["differentiators"]) == 6
    for capability in catalog["datahub_capabilities"]:
        assert Path(capability["implementation"]).is_file()
        assert Path(capability["proof"]).is_file()


def test_technology_api_is_judge_inspectable(tmp_path) -> None:
    response = TestClient(create_app(tmp_path)).get("/api/technology")
    assert response.status_code == 200
    payload = response.json()
    assert payload == technology_catalog()
    assert payload["open_source_contribution"]["status"] == "merged"


def test_landing_makes_datahub_backend_and_novelty_unmissable(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert 'id="datahub-stack"' in text
    assert "DataHub is the reasoning substrate&mdash;not a logo in the footer." in text
    for surface in (
        "Fine-grained lineage",
        "Downstream graph",
        "Python SDK",
        "GraphQL API",
        "MCP Server",
        "DataHub Skill",
        "Governed write-back",
    ):
        assert surface in text
    assert "What Mosaic adds beyond DataHub out of the box" in text
    assert "Merged into DataHub" in text
    assert 'href="/api/technology"' in text


def test_readme_explains_sponsor_usage_as_architecture_not_marketing() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## How Mosaic uses DataHub" in text
    assert "DataHub is the reasoning substrate" in text
    assert "### What Mosaic adds beyond DataHub" in text
    assert "### Supporting technology" in text
    assert "datahub-project/datahub#18705" in text
