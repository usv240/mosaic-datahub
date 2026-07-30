from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def verify(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    claimed = payload.pop("sha256", None)
    actual = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "status": "verified" if claimed == actual else "failed",
        "claimed_sha256": str(claimed),
        "actual_sha256": actual,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a retained Mosaic evidence bundle")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    report = verify(args.path)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
