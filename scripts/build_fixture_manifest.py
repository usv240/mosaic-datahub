from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1] / "fixtures" / "datahub_recording"


def main() -> None:
    files = []
    for path in sorted((ROOT / "responses").glob("*.json")):
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "fixture_id": "mosaic-datahub-recording-v1",
        "description": "Sanitized metadata-only recording of Mosaic's synthetic live workflow.",
        "captured_at": "2026-07-29",
        "captured_from": {
            "datahub_core": "1.5.0.6",
            "datahub_sdk": "1.6.0.16",
            "mcp_server_datahub": "0.6.0",
        },
        "safety": {"synthetic_only": True, "raw_person_rows": 0},
        "files": files,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
