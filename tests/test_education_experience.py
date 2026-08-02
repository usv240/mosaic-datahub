from fastapi.testclient import TestClient

from mosaic.web.complete_app import create_app


def test_first_time_visitor_gets_plain_language_orientation(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert "no privacy background needed" in text
    assert "Safe alone does not mean safe together" in text
    assert "DataHub supplies the missing map" in text
    assert "Mosaic counts groups, never identifies people" in text
    assert "k=1 means one unique record" in text
    assert "how many records share this combination?" in text


def test_guided_demo_has_live_explanatory_narration(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    assert 'id="narrator"' in text
    assert 'id="narrator-title"' in text
    assert 'id="narrator-body"' in text
    assert 'id="narrator-why"' in text
    assert 'aria-atomic="true"' in text
    assert "We will explain each catalog read" in text


def test_every_specialist_term_has_a_plain_english_definition(tmp_path) -> None:
    text = TestClient(create_app(tmp_path)).get("/").text
    for term in (
        "DataHub lineage",
        "Quasi-identifier",
        "Minimum k",
        "Aggregate-only query",
        "Blast radius",
        "Governed write-back",
    ):
        assert f"<summary>{term}" in text
    assert text.count("<details>") == 6


def test_each_agent_step_explains_action_and_significance(tmp_path) -> None:
    script = TestClient(create_app(tmp_path)).get("/static/experience.js").text
    for step in (
        "Step 1 - Discover",
        "Step 2 - Converge",
        "Step 3 - Validate",
        "Step 4 - Defend",
        "Step 5 - Mitigate",
        "Step 6 - Generate",
    ):
        assert step in script
    assert script.count("why:") >= 9
    assert "What this proves" in script
    assert "The page will not move you without permission" in script


def test_negative_control_receives_its_own_educational_story(tmp_path) -> None:
    script = TestClient(create_app(tmp_path)).get("/static/experience.js").text
    assert "No person-joinable combination exists" in script
    assert "No data query is needed" in script
    assert "negative control stays clear" in script
    assert "proposes no catalog mutation" in script
