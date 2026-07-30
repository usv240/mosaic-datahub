from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def record(bundle: dict[str, object], directory: Path) -> dict[str, object]:
    """Persist an immutable evidence bundle with its content digest."""
    directory.mkdir(parents=True, exist_ok=True)
    payload = dict(bundle)
    recorded_at = datetime.now(UTC)
    payload["run_id"] = f"mosaic-{recorded_at:%Y%m%dT%H%M%S%f}-{uuid4().hex[:6]}"
    payload["recorded_at"] = recorded_at.isoformat()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["sha256"] = hashlib.sha256(canonical).hexdigest()
    (directory / f"{payload['run_id']}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def list_runs(directory: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(directory.glob("mosaic-*.json"), reverse=True) if directory.exists() else []:
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return rows
