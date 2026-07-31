from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_sha256(value: Any) -> str:
    """Hash JSON meaning, not platform-specific whitespace or line endings."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
