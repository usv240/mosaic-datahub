from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mosaic.web.complete_app import create_app


def test_landing_page_is_an_interactive_preset_demo(tmp_path) -> None:
    page = TestClient(create_app(tmp_path)).get("/")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert page.text.count('class="preset-card') == 4
    assert 'data-scenario="audience"' in page.text
    assert 'data-scenario="research"' in page.text
    assert 'data-scenario="mitigated"' in page.text
    assert 'data-scenario="control"' in page.text
    assert 'id="run-demo"' in page.text
    assert 'id="activity-log"' in page.text
    assert 'id="query-code"' in page.text
    assert 'id="proposal-risk"' in page.text


def test_landing_page_has_complete_accessible_workspace(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert '<a class="skip-link" href="#main">' in text
    assert 'aria-label="Investigation progress"' in text
    assert 'role="tablist"' in text
    assert 'aria-live="polite"' in text
    assert "prefers-reduced-motion" not in text  # Kept in CSS, not inline markup.
    assert "This hosted experience is intentionally read-only" in text


def test_experience_assets_are_served_and_free_of_mojibake(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    paths = (
        "/",
        "/runs",
        "/static/experience.css",
        "/static/experience.js",
        "/static/runs.css",
        "/static/runs.js",
    )
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert not any(
            token in response.text for token in ("\u00c3", "\u00e2", "\u00c2", "\u00f0\u0178")
        ), path


def test_theme_and_responsive_modes_are_first_class(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    css = client.get("/static/experience.css").text
    script = client.get("/static/experience.js").text
    assert ':root[data-theme="light"]' in css
    assert "@media (max-width: 760px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "mosaic-theme" in script
    assert "prefers-color-scheme: light" in script


def test_evidence_workspace_keeps_current_proof_visible_without_saved_runs(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    text = client.get("/runs").text
    assert "Every verdict keeps its receipts" in text
    assert "Current deterministic fixture" in text
    assert "/api/assessment" in text
    assert "/api/mitigations" in text
    assert "Retained evidence bundles" in text


def test_demo_javascript_contains_all_guided_steps(tmp_path) -> None:
    script = TestClient(create_app(tmp_path)).get("/static/experience.js").text
    for step in (
        "Read 3 column-lineage paths",
        "Mapped location, date-of-birth, and demographic families",
        "Executed allowlisted GROUP BY",
        "Compared 3 reversible mitigations",
        "Prepared governed DataHub proposal",
    ):
        assert step in script


def test_demo_fetches_real_engine_evidence_instead_of_faking_metrics(tmp_path) -> None:
    script = TestClient(create_app(tmp_path)).get("/static/experience.js").text
    assert 'fetch("/api/assessment")' in script
    assert 'fetch("/api/mitigations")' in script
    assert "assessment.metrics.minimum_k" in script
    assert "assessment.raw_rows_returned" not in script  # Raw rows never enter the demo model.


def test_default_landing_does_not_rewrite_itself_to_workspace_deep_link(tmp_path) -> None:
    script = TestClient(create_app(tmp_path)).get("/static/experience.js").text
    guarded_url_update = (
        "if (shouldScroll) {\n"
        '      if (history.replaceState) history.replaceState(null, "", "?case=" + name + "#workspace");'
    )
    assert guarded_url_update in script.replace("\r\n", "\n")
    accessibility = Path("scripts/check_accessibility.py").read_text(encoding="utf-8")
    assert "landing did not open cleanly at top" in accessibility
