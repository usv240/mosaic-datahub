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
    benchmark = run("benchmark")
    replay = run("replay-fixture")
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
    assert benchmark["status"] == "passed"
    assert replay["status"] == "passed"
    assert generated["artifact_count"] == 6
    assert generated["track"] == "Metadata-Aware Code Generation & Development"
    print(
        "CLI contracts passed: verdicts, estate scan, benchmark, fixture replay, and remediation codegen."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
