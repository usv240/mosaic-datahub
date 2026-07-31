from __future__ import annotations

import json
from pathlib import Path

from mosaic.canonical import canonical_json_sha256
from mosaic.policy import load_policy


def test_canonical_json_digest_ignores_layout_and_line_endings() -> None:
    value = {"nested": {"enabled": True}, "threshold": 5}
    pretty_lf = json.dumps(value, indent=2) + "\n"
    pretty_crlf = pretty_lf.replace("\n", "\r\n")
    assert canonical_json_sha256(json.loads(pretty_lf)) == canonical_json_sha256(
        json.loads(pretty_crlf)
    )


def test_policy_digest_is_semantic_across_line_endings(tmp_path: Path) -> None:
    source = Path(".mosaic/privacy-policy.yml").read_text(encoding="utf-8")
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    lf_path.write_text(source.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    crlf_path.write_text(source.replace("\r\n", "\n"), encoding="utf-8", newline="\r\n")
    assert load_policy(lf_path).sha256 == load_policy(crlf_path).sha256
