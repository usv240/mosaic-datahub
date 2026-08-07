from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args: str, expected: int = 0) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "mosaic.final_cli", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != expected:
        raise RuntimeError(
            f"{' '.join(args)} returned {completed.returncode}, expected {expected}: {completed.stderr}"
        )
    return json.loads(completed.stdout)


def main() -> int:
    critical = run("demo", "--json", expected=3)
    scan = run("scan", expected=3)
    gate = run("check", "--fail-on", "critical", expected=3)
    benchmark = run("benchmark")
    replay = run("replay-fixture")
    redteam = run("redteam")
    byod_critical = run(
        "measure",
        "--csv",
        "examples/bring-your-own-data/risky_member_export.csv",
        "--columns",
        "zip5,birth_date,gender",
        expected=3,
    )
    byod_clear = run(
        "measure",
        "--csv",
        "examples/bring-your-own-data/safe_member_export.csv",
        "--columns",
        "region,age_band,gender",
    )
    agent_accepted = run("assess", "--agent", "--replay", "--scenario", "research", expected=3)
    agent_vetoed = run(
        "assess",
        "--agent",
        "--replay",
        "fixtures/agent_transcripts/vetoed.json",
        "--scenario",
        "research",
        expected=2,
    )
    with tempfile.TemporaryDirectory() as directory:
        generated = run(
            "generate-remediation",
            "--scenario",
            "research",
            "--output",
            str(Path(directory) / "remediation"),
        )
    assert critical["assessment"]["verdict"] == "validated_critical"
    assert scan["critical_findings"] >= 1
    assert gate["status"] == "failed"
    assert gate["raw_person_rows_returned"] == 0
    assert benchmark["status"] == "passed"
    assert replay["status"] == "passed"
    assert generated["artifact_count"] == 6
    assert generated["track"] == "Metadata-Aware Code Generation & Development"
    assert byod_critical["status"] == "validated_critical"
    assert byod_critical["metrics"]["minimum_k"] == 1
    assert byod_critical["privacy"]["raw_person_rows_returned"] == 0
    assert byod_clear["status"] == "validated_low"
    assert byod_clear["metrics"]["minimum_k"] >= 5
    assert redteam["status"] == "passed"
    assert redteam["controls"]["policy_refused_requested_sql"] is True
    assert redteam["controls"]["raw_person_rows_returned"] == 0
    assert agent_accepted["status"] == "accepted_for_human_review"
    assert agent_accepted["model"]["execution"] == "replayed_recorded_response"
    assert agent_accepted["verification"]["generated_code_executed"] is False
    assert agent_vetoed["status"] == "vetoed"
    assert agent_vetoed["verification"]["policy_veto"] is True
    assert agent_vetoed["verification"]["compiled_aggregate_query"] is None
    print(
        "CLI contracts passed: verdicts, estate scan, pre-merge gate, benchmark, fixture replay, "
        "red-team veto, zero-setup agent replay, bring-your-own-data measurement, and remediation codegen."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
