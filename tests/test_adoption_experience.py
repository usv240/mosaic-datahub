from pathlib import Path

from fastapi.testclient import TestClient

from mosaic.adoption import adoption_catalog
from mosaic.web.complete_app import create_app


def test_adoption_catalog_is_honest_and_actionable() -> None:
    catalog = adoption_catalog()
    assert catalog["status"] == "ready_to_evaluate"
    assert [audience["id"] for audience in catalog["audiences"]] == [
        "privacy",
        "data",
        "governance",
        "security",
    ]
    assert [path["readiness"] for path in catalog["paths"]] == [
        "available_now",
        "available_now",
        "configuration_required",
        "production_hardening_required",
    ]
    assert catalog["connectors"][2]["status"] == "integration_required"
    assert len(catalog["production_gates"]) == 5


def test_adoption_api_is_publicly_inspectable(tmp_path) -> None:
    response = TestClient(create_app(tmp_path)).get("/api/adoption")
    assert response.status_code == 200
    assert response.json() == adoption_catalog()


def test_landing_leads_with_impact_and_an_honest_adoption_path(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert 'id="impact"' in text
    assert 'id="adopt"' in text
    assert "Stop a risky release before it becomes an incident" in text
    assert "Built for every team around governed data" in text
    assert "Start without credentials. Grow without replacing the workflow." in text
    assert "Production hardening required" in text
    assert 'href="/settings#readiness"' in text


def test_settings_contains_a_machine_backed_readiness_planner(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    page = client.get("/settings")
    script = client.get("/static/settings.js")
    assert 'id="readiness"' in page.text
    assert 'id="adoption-paths"' in page.text
    assert 'id="connector-matrix"' in page.text
    assert 'fetch("/api/adoption")' in script.text
    assert "integration_required" in script.text


def test_csp_compatible_theme_boot_has_no_inline_script(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert "localStorage.getItem" not in text
    assert '<script defer src="/static/experience.js"></script>' in text


def test_one_command_container_evaluation_defaults_to_read_only() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    environment = Path(".env.example").read_text(encoding="utf-8")
    guide = Path("docs/ADOPTION_GUIDE.md").read_text(encoding="utf-8")
    assert 'MOSAIC_PUBLIC_DEMO: "true"' in compose
    assert "docker compose up --build" in guide
    assert "MOSAIC_ENABLE_WEB_WRITEBACK=false" in environment
    assert "integration boundaries, not claimed built-in connectors" in guide
    capture = Path("scripts/capture_submission_media.py").read_text(encoding="utf-8")
    assert "data-has-integration-boundary" in capture
    assert "08-datahub-architecture.png" in capture
    workflow = Path(".github/workflows/verify.yml").read_text(encoding="utf-8")
    assert "Smoke production container" in workflow
    assert "/api/adoption" in workflow
    assert "/api/technology" in workflow
    assert "\n      - name: Browser accessibility gate" in workflow
