from __future__ import annotations

import argparse
import json
from pathlib import Path

from mosaic.complete_e2e import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Mosaic's complete synthetic live workflow")
    parser.add_argument("--server", default="http://localhost:8080")
    parser.add_argument("--approve-writeback", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("evidence/complete.local.json"))
    args = parser.parse_args()
    report = run(args.server, approve_writeback=args.approve_writeback)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
