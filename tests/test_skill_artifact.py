from __future__ import annotations

import importlib.util
from pathlib import Path

from mosaic.runs import record
from mosaic.scenario_registry import assess_scenario

SKILL = Path("skills/datahub-privacy-threat-model")


def _verifier():
    path = SKILL / "scripts/verify_evidence.py"
    spec = importlib.util.spec_from_file_location("verify_evidence", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skill_has_complete_interface_and_safety_reference() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    interface = (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
    assert "TODO" not in skill
    assert "raw rows returned (`0`)" in skill
    assert "$datahub-privacy-threat-model" in interface
    assert (SKILL / "references/safety-and-evidence.md").is_file()


def test_skill_verifier_accepts_retained_bundle(tmp_path) -> None:
    saved = record(assess_scenario("research"), tmp_path)
    report = _verifier().verify(tmp_path / f"{saved['run_id']}.json")
    assert report["status"] == "verified"
