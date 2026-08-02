from __future__ import annotations

import hashlib
import json
from pathlib import Path


def test_submission_video_is_current_reproducible_and_under_three_minutes() -> None:
    receipt = json.loads(
        Path("docs/demo/submission-video-receipt.json").read_text(encoding="utf-8")
    )
    video = Path(receipt["path"])
    builder = Path("scripts/build_submission_video.py").read_text(encoding="utf-8")
    capture = Path("scripts/capture_submission_media.py").read_text(encoding="utf-8")

    assert receipt["status"] == "upload_ready"
    assert receipt["duration_seconds"] < receipt["duration_limit_seconds"] == 180
    assert receipt["scene_count"] == 11
    assert receipt["video"] == {
        "codec": "h264",
        "width": 1280,
        "height": 720,
        "frames_per_second": 24,
    }
    assert receipt["audio"]["codec"] == "aac"
    assert receipt["bytes"] == video.stat().st_size
    assert receipt["sha256"] == hashlib.sha256(video.read_bytes()).hexdigest()
    assert '"-pix_fmt"' in builder and '"yuv420p"' in builder
    assert "xfade=transition=fade" in builder
    for index in range(1, 12):
        token = f"video-{index:02d}-"
        assert token in builder
        assert token in capture


def test_public_video_receipt_is_explicit_until_uploaded() -> None:
    receipt = json.loads(
        Path("docs/demo/submission-video-receipt.json").read_text(encoding="utf-8")
    )
    if receipt["public_url"] is None:
        assert receipt["public_upload_status"] == "pending_authenticated_youtube_or_vimeo_session"
    else:
        assert receipt["public_upload_status"] == "complete"
        assert receipt["public_url"].startswith(
            ("https://www.youtube.com/", "https://youtu.be/", "https://vimeo.com/")
        )
