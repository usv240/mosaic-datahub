from __future__ import annotations

import json
from pathlib import Path

ROOTS = (
    Path("evaluations"),
    Path("evidence"),
    Path("fixtures"),
    Path("src/mosaic/scenario_specs"),
    Path("examples/generated"),
)


def main() -> int:
    paths = sorted(path for root in ROOTS if root.exists() for path in root.rglob("*.json"))
    if not paths:
        raise SystemExit("no JSON deliverables found")
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))
    print(f"Strict JSON check passed: {len(paths)} artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
