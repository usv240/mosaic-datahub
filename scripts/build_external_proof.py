from __future__ import annotations

import argparse
import json
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

from mosaic.external_proof import build_adult_proof

OFFICIAL_ARCHIVE = "https://archive.ics.uci.edu/static/public/2/adult.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Mosaic's aggregate-only UCI Adult proof")
    parser.add_argument("--archive", type=Path, help="Optional local Adult ZIP")
    parser.add_argument(
        "--output", type=Path, default=Path("evidence/external/uci-adult-proof.json")
    )
    args = parser.parse_args()

    archive = (
        args.archive.read_bytes()
        if args.archive
        else urllib.request.urlopen(OFFICIAL_ARCHIVE).read()
    )
    with zipfile.ZipFile(BytesIO(archive)) as zipped:
        data = zipped.read("adult.data")
    report = build_adult_proof(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
