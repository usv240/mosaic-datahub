from __future__ import annotations

import json
from pathlib import Path

from mosaic.benchmark import run_benchmark


def main() -> None:
    output = Path(__file__).parents[1] / "evaluations" / "benchmark.json"
    output.write_text(json.dumps(run_benchmark(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
