from __future__ import annotations

from pathlib import Path

SKILL = Path("skills/datahub-privacy-threat-model")


def main() -> int:
    required = (
        SKILL / "SKILL.md",
        SKILL / "agents/openai.yaml",
        SKILL / "references/safety-and-evidence.md",
        SKILL / "scripts/verify_evidence.py",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("Missing skill resources: " + ", ".join(missing))
    skill = required[0].read_text(encoding="utf-8")
    interface = required[1].read_text(encoding="utf-8")
    if not skill.startswith("---\nname: datahub-privacy-threat-model\ndescription:"):
        raise SystemExit("Invalid SKILL.md frontmatter")
    if "TODO" in skill or "$datahub-privacy-threat-model" not in interface:
        raise SystemExit("Skill interface contains placeholders or lacks its invocation prompt")
    print("Packaged DataHub skill structure passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
