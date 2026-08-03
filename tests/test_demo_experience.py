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
    assert '<section class="narrator" id="narrator" tabindex="-1"' in text
    assert 'id="advance-demo-step" hidden' in text


def test_metric_help_is_visible_accessible_and_touch_friendly(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    landing = client.get("/").text
    css = client.get("/static/experience.css").text
    script = client.get("/static/experience.js").text
    browser_gate = Path("scripts/check_accessibility.py").read_text(encoding="utf-8")

    assert 'aria-describedby="metric-k-help"' in landing
    assert 'aria-controls="metric-k-help"' in landing
    assert 'id="metric-k-help" role="tooltip"' in landing
    assert "lower singling-out risk in this demo" in landing
    assert "data-tip" not in landing
    assert ".metric-stack .help-tooltip{position:absolute;left:0;right:auto" in css
    assert "@media(hover:hover)" in css
    assert "@media(pointer:coarse){.help{width:32px;height:32px" in css
    assert "function initHelpTips()" in script
    assert 'event.key !== "Escape"' in script
    assert 'button.setAttribute("aria-expanded", "true")' in script
    for contract in (
        "metric help tooltip did not open on hover",
        "metric help tooltip did not open on keyboard focus",
        "Escape did not dismiss help while retaining trigger focus",
        "metric help click did not pin the tooltip",
        "mobile metric help target or popover regressed",
    ):
        assert contract in browser_gate


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
        "Generated 6 merge-ready artifacts",
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
        '      if (history.replaceState) history.replaceState(null, "", "?case=" + name);'
    )
    normalized = script.replace("\r\n", "\n")
    assert guarded_url_update in normalized
    assert '"?case=" + name + "#workspace"' not in normalized
    accessibility = Path("scripts/check_accessibility.py").read_text(encoding="utf-8")
    assert "landing did not open cleanly at top" in accessibility


def test_visual_demo_contracts_keep_proofs_readable(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    css = client.get("/static/experience.css").text
    script = client.get("/static/experience.js").text
    capture = Path("scripts/capture_submission_media.py").read_text(encoding="utf-8")
    assert (
        ".extraordinary-block>.cross-asset-proof,.extraordinary-block>.agent-proof{grid-column:1/-1}"
        in css
    )
    assert ".hero::before{width:100%;left:0}" in css
    assert ".evidence-tabs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))" in css
    assert "var delay" not in script
    assert "function advanceDemoStep()" in script
    assert "function finishDemo()" in script
    assert 'setStepControlLabel("Continue to step " + nextStep' in script
    progression = script.split("function setStepControlLabel", 1)[1].split("function resetDemo", 1)[
        0
    ]
    assert "setTimeout" not in progression
    assert "setInterval" not in progression
    assert "messages.forEach" not in progression
    assert "12-attack-refusal.png" in capture
    assert "for _ in range(5)" in capture
    assert capture.count("_finish_selected_case(") == 6
    assert 'locator("#run-demo").click()' not in capture
    assert 'locator("#run-tour-case").click()' not in capture


def test_manual_case_explorer_proves_all_scenarios_and_adoption(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    landing = client.get("/").text
    script = client.get("/static/experience.js").text
    for token in (
        'id="run-all-scenarios"',
        'id="tour-controller"',
        'data-tour-scenario="research"',
        'data-tour-scenario="mitigated"',
        'data-tour-scenario="control"',
        'data-tour-scenario="audience"',
        'id="tour-summary"',
        'aria-live="polite"',
        'tabindex="-1"',
        'href="/settings#readiness"',
        'href="/runs"',
    ):
        assert token in landing
    assert 'var tourOrder = ["research", "mitigated", "control", "audience"]' in script
    assert 'byId("hero-run").addEventListener("click", openCasePicker)' in script
    assert 'byId("run-tour-case").addEventListener("click", runSelectedTourCase)' in script
    assert 'byId("advance-demo-step").addEventListener("click", advanceDemoStep)' in script
    assert 'byId("next-tour-case").addEventListener("click", nextTourScenario)' in script
    assert 'byId("compare-tour").addEventListener("click", showTourSummary)' in script
    assert 'byId("reset-demo").addEventListener("click", resetSelectedCase)' in script
    assert 'byId("tour-summary").focus({ preventScroll: true })' in script
    assert "setTimeout(runTourScenario" not in script
    assert "tourTimer" not in script
    assert "Nothing runs until you press Start selected case." in script
    assert "Start reveals step 1. Each later step waits for Continue." in landing
    assert "new AbortController()" in script
    assert 'fetch("/api/redteam", { signal: controller.signal })' in script
    assert "controller.abort(); }, 4_000" in script
    assert 'if (selected === "research") selectScenario' not in script
    assert "requestId === codegenRequestId" in script
    assert "runTimers" not in script
    assert "messages.forEach" not in script
    assert "Verified clear / no data query" in script
    assert "Read the original and shadow lineage" in script
    assert "Read lineage across a second business domain" in script
    accessibility = Path("scripts/check_accessibility.py").read_text(encoding="utf-8")
    capture = Path("scripts/capture_submission_media.py").read_text(encoding="utf-8")
    assert "verified_cases != 4" in accessibility
    assert 'journey.locator("#narrator-step").text_content() != "Step 1 of 6"' in accessibility
    assert accessibility.count("journey.wait_for_timeout(2_200)") == 2
    assert "late hydration reset an active demo" in accessibility
    assert "failed policy receipt deadlocked or advanced the demo" in accessibility
    assert 'page.locator("#advance-demo-step").click' in capture
    assert "13-four-case-scorecard.png" in capture
