"""Derive replayable agent transcripts from the recorded local-model receipts.

The transcripts reproduce the exact envelope an Ollama-compatible endpoint returned,
so `mosaic assess --agent --replay` exercises the real parsing, verification, and veto
path with only the network call substituted. Nothing here is hand-authored: every
proposal is copied verbatim from the committed live receipt.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = (
    ("accepted", ROOT / "evidence" / "external" / "ollama-agent-accepted-live.json"),
    ("vetoed", ROOT / "evidence" / "external" / "ollama-agent-veto-live.json"),
)
TRANSCRIPT_ROOT = ROOT / "fixtures" / "agent_transcripts"


def _envelope(receipt: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the provider envelope; `response` is the model's raw structured output."""
    telemetry = receipt["model"]
    raw = json.dumps(receipt["proposal"], separators=(",", ":"), sort_keys=True)
    return {
        "model": telemetry["model"],
        "done": telemetry["done"],
        "prompt_eval_count": telemetry["prompt_eval_count"],
        "eval_count": telemetry["eval_count"],
        "response": raw,
    }


def build(name: str, receipt_path: Path) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    envelope = _envelope(receipt)
    return {
        "schema_version": 1,
        "provider": receipt["model"]["provider"],
        "captured_from": receipt_path.relative_to(ROOT).as_posix(),
        "expected_status": receipt["status"],
        "expected_veto_reasons": receipt["verification"]["veto_reasons"],
        "response_sha256": hashlib.sha256(envelope["response"].encode("utf-8")).hexdigest(),
        "response": envelope,
    }


def main() -> int:
    TRANSCRIPT_ROOT.mkdir(parents=True, exist_ok=True)
    for name, receipt_path in RECEIPTS:
        transcript = build(name, receipt_path)
        target = TRANSCRIPT_ROOT / f"{name}.json"
        target.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{target.relative_to(ROOT).as_posix()}: {transcript['expected_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
