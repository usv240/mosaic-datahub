from pathlib import Path


def test_research_foundations_map_sources_to_inspectable_controls() -> None:
    research = Path("docs/RESEARCH_FOUNDATIONS.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    landing = Path("src/mosaic/web/experience.html").read_text(encoding="utf-8")
    for source in (
        "datahub.com/blog/build-with-datahub-agent-hackathon",
        "datahub.com/resources/datahub-mcp-server-overview",
        "docs.getdbt.com/docs/mesh/govern/model-contracts",
        "docs.getdbt.com/docs/build/data-tests",
        "nist.gov/publications/de-identification-personal-information",
        "cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet",
    ):
        assert source in research
    assert "claim-to-control research map" in readme
    assert "Built on standards, not vibes" in landing
    assert "None is presented as certification" in landing


def test_skill_carries_codegen_trust_and_review_contract() -> None:
    skill = Path("skills/datahub-privacy-threat-model/SKILL.md").read_text(encoding="utf-8")
    assert "allowlisted structured DataHub context" in skill
    assert "enforced typed contract" in skill
    assert "never commit, merge, or execute" in skill
    assert "generate-remediation" in skill
