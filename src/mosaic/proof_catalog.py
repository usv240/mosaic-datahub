from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mosaic.fixture_replay import replay_fixture


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def proof_catalog(root: Path) -> dict[str, Any]:
    benchmark = _read(root / "evaluations/benchmark.json")
    external = _read(root / "evidence/external/uci-adult-proof.json")
    replay = replay_fixture(root / "fixtures/datahub_recording")
    return {
        "schema_version": 1,
        "status": "passed"
        if benchmark["status"] == external["status"] == replay["status"] == "passed"
        else "failed",
        "proofs": [
            {
                "id": "regression",
                "label": "Policy regression",
                "headline": f"{benchmark['cases']} exact cases",
                "status": benchmark["status"],
                "metrics": benchmark["metrics"],
                "integrity": benchmark["repeatability_sha256"],
                "scope": benchmark["disclosure"]["what_is_by_construction"],
            },
            {
                "id": "datahub-replay",
                "label": "DataHub integration",
                "headline": f"{sum(replay['checks'].values())}/{len(replay['checks'])} semantic checks",
                "status": replay["status"],
                "metrics": replay["checks"],
                "integrity": all(replay["integrity"].values()),
                "scope": "Versioned, sanitized DataHub SDK, GraphQL, MCP, lineage, downstream, and write-back semantics.",
            },
            {
                "id": "external-data",
                "label": "External mechanism proof",
                "headline": f"{external['source']['records_processed_in_memory']:,} records",
                "status": external["status"],
                "metrics": {
                    "single_attribute_minimum_k": external["single_attribute_control"]["minimum_k"],
                    "composed_minimum_k": external["composed_attributes"]["minimum_k"],
                    "composed_percent_below_5": external["composed_attributes"]["percent_below_5"],
                    "raw_rows_committed": external["source"]["raw_rows_committed"],
                },
                "integrity": external["source"]["source_sha256"],
                "scope": external["method"]["limitations"],
            },
        ],
        "contribution": {
            "status": "merged",
            "url": "https://github.com/datahub-project/datahub/pull/18705",
            "label": "DataHub open-source contribution #18705",
        },
    }
