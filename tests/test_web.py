from fastapi.testclient import TestClient

from mosaic.web import create_app


def test_landing_page_leads_with_plain_language_problem() -> None:
    text = TestClient(create_app()).get("/").text
    assert "No column here is PII" in text
    assert "Together, they identify you" in text
    assert "DataHub" in text
    assert 'id="theme"' in text
    assert 'id="graph"' in text


def test_evidence_api_is_complete_and_safe() -> None:
    data = TestClient(create_app()).get("/api/assessment").json()
    assert data["assessment"]["raw_rows_returned"] == 0
    assert data["safe_controls"]["status"] == "passed"
    assert data["graph_value"]["status"] == "passed"


def test_health() -> None:
    assert TestClient(create_app()).get("/health").json() == {"status": "ok"}
