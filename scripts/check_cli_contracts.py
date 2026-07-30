from __future__ import annotations

import json
import subprocess
import sys


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
    assert critical["assessment"]["verdict"] == "validated_critical"
    assert scan["critical_findings"] >= 1
    assert benchmark["status"] == "passed"
    assert replay["status"] == "passed"
    print("CLI contracts passed: verdict exit codes, estate scan, benchmark, and fixture replay.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
