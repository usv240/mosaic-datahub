from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import wave
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "artifacts" / "submission-media"
DEMO = ROOT / "docs" / "demo"
OUTPUT = DEMO / "mosaic-submission-demo.mp4"
NARRATION = DEMO / "narration.wav"
RECEIPT = DEMO / "submission-video-receipt.json"
NARRATION_TEXT = DEMO / "narration.txt"
SCENES = [
    ("video-01-hero.png", 33),
    ("video-02-lineage.png", 53),
    ("video-03-four-decisions.png", 42),
    ("video-04-cross-asset.png", 30),
    ("video-05-measured-result.png", 47),
    ("video-06-agent-boundary.png", 48),
    ("video-07-attack-refusal.png", 38),
    ("video-08-generated-pr.png", 60),
    ("video-09-datahub-stack.png", 51),
    ("video-10-external-evidence.png", 41),
    ("video-11-production-readiness.png", 52),
]
DURATION_LIMIT_SECONDS = 180
TRANSITION_SECONDS = 0.6


def narration_duration() -> float:
    """Length of the rendered narration, which is what the scene timings must match.

    Hardcoding this drifts the moment the script is reworded: a longer take gets
    trimmed mid-sentence, a shorter one ends on silence. Reading the audio keeps
    the two in step and enforces the submission's three-minute ceiling.
    """
    with wave.open(str(NARRATION), "rb") as handle:
        seconds = handle.getnframes() / float(handle.getframerate())
    if seconds > DURATION_LIMIT_SECONDS:
        raise RuntimeError(
            f"narration is {seconds:.2f}s; the submission limit is {DURATION_LIMIT_SECONDS}s"
        )
    return seconds


def check_scene_word_counts() -> None:
    """Scene durations are proportional to per-scene word counts, so they must agree."""
    if not NARRATION_TEXT.is_file():
        return
    paragraphs = [
        block.strip()
        for block in NARRATION_TEXT.read_text(encoding="utf-8").split("\n\n")
        if block.strip()
    ]
    actual = [len(block.split()) for block in paragraphs]
    declared = [words for _name, words in SCENES]
    if actual != declared:
        raise RuntimeError(
            f"narration.txt has word counts {actual}, but SCENES declares {declared}; "
            "update SCENES so scene timings track the narration"
        )


def ffmpeg_executable() -> str:
    configured = os.getenv("MOSAIC_FFMPEG")
    if configured:
        return configured
    installed = shutil.which("ffmpeg")
    if installed:
        return installed
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as error:
        raise RuntimeError(
            "ffmpeg is required; install it or run `uv run --with imageio-ffmpeg "
            "python scripts/build_submission_video.py`"
        ) from error


def build() -> Path:
    missing = [str(MEDIA / name) for name, _words in SCENES if not (MEDIA / name).is_file()]
    if missing:
        raise RuntimeError("capture submission media first; missing: " + ", ".join(missing))
    if not NARRATION.is_file():
        raise RuntimeError(f"missing narration: {NARRATION}")
    check_scene_word_counts()
    duration_seconds = narration_duration()

    total_words = sum(words for _name, words in SCENES)
    segments = [duration_seconds * words / total_words for _name, words in SCENES]
    command = [ffmpeg_executable(), "-y", "-hide_banner", "-loglevel", "error"]
    for index, ((name, _words), duration) in enumerate(zip(SCENES, segments, strict=True)):
        input_duration = duration + (TRANSITION_SECONDS if index < len(SCENES) - 1 else 0)
        command.extend(["-loop", "1", "-t", f"{input_duration:.5f}", "-i", str(MEDIA / name)])
    command.extend(["-i", str(NARRATION)])

    filters = []
    for index in range(len(SCENES)):
        filters.append(
            f"[{index}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x080b14,"
            f"setsar=1,fps=24,format=yuv420p[v{index}]"
        )
    previous = "v0"
    elapsed = segments[0]
    for index in range(1, len(SCENES)):
        output = f"mix{index}"
        filters.append(
            f"[{previous}][v{index}]xfade=transition=fade:duration={TRANSITION_SECONDS}:"
            f"offset={elapsed:.5f}[{output}]"
        )
        previous = output
        elapsed += segments[index]

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            f"[{previous}]",
            "-map",
            f"{len(SCENES)}:a:0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-r",
            "24",
            "-t",
            f"{duration_seconds:.5f}",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ]
    )
    DEMO.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True)
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    existing = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else {}
    receipt = {
        "schema_version": 1,
        "status": "upload_ready",
        "built_at": datetime.now(UTC).isoformat(),
        "path": "docs/demo/mosaic-submission-demo.mp4",
        "duration_seconds": round(duration_seconds, 2),
        "duration_limit_seconds": DURATION_LIMIT_SECONDS,
        "video": {"codec": "h264", "width": 1280, "height": 720, "frames_per_second": 24},
        "audio": {"codec": "aac", "channels": 1, "sample_rate_hz": 22050},
        "scene_count": len(SCENES),
        "bytes": OUTPUT.stat().st_size,
        "sha256": digest,
        "public_url": existing.get("public_url"),
        "public_upload_status": (
            "complete"
            if existing.get("public_url")
            else "pending_authenticated_youtube_or_vimeo_session"
        ),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size} bytes, sha256 {digest}).")
    return OUTPUT


if __name__ == "__main__":
    try:
        build()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
