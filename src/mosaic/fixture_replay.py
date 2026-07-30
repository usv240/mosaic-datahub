from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def replay_fixture(root: Path) -> dict[str, Any]:
    manifest = _read(root / "manifest.json")
    integrity = {}
    payloads = {}
    for entry in manifest["files"]:
        path = root / entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        integrity[entry["path"]] = digest == entry["sha256"]
        payloads[entry["path"]] = _read(path)

    entity = payloads["responses/entity.json"]
    lineage = payloads["responses/lineage.json"]
    downstream = payloads["responses/downstream.json"]
    writeback = payloads["responses/writeback.json"]
    mcp = payloads["responses/mcp.json"]
    checks = {
        "manifest_integrity": all(integrity.values()),
        "schema_contains_quasi_identifiers": {"zip5", "birth_date", "gender_category"}
        <= set(entity["schema_fields"]),
        "three_independent_lineage_paths": len(lineage["paths"]) == 3
        and len({path["source_asset"] for path in lineage["paths"]}) >= 2,
        "downstream_blast_radius_reread": len(downstream["assets"]) == 3,
        "governed_writeback_reread": all(writeback["checks"].values()),
        "official_mcp_contract": {"search", "get_entities", "get_lineage", "add_tags"}
        <= set(mcp["available_tools"])
        and all(mcp["checks"].values()),
        "zero_raw_rows": manifest["safety"]["raw_person_rows"] == 0,
    }
    return {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "status": "passed" if all(checks.values()) else "failed",
        "captured_at": manifest["captured_at"],
        "captured_from": manifest["captured_from"],
        "checks": checks,
        "integrity": integrity,
        "raw_rows_returned": 0,
    }
