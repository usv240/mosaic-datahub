from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "submission-manifest.json"
PUBLIC_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "vimeo.com",
    "www.vimeo.com",
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _json_url(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "mosaic-submission-audit/1"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def audit(
    *,
    online: bool = False,
    allow_pending_video: bool = False,
) -> list[Check]:
    manifest = _load_json(MANIFEST)
    receipt_path = ROOT / str(manifest["video_receipt"])
    receipt = _load_json(receipt_path)
    video_path = ROOT / str(receipt["path"])
    public_url = receipt.get("public_url")
    public_host = urlparse(str(public_url)).hostname if public_url else None
    head = _git("rev-parse", "HEAD")
    remote = _git("remote", "get-url", "origin")
    contribution = manifest["contribution"]
    assert isinstance(contribution, dict)

    checks = [
        Check(
            "track",
            manifest.get("track") == "Metadata-Aware Code Generation & Development",
            str(manifest.get("track")),
        ),
        Check(
            "license",
            manifest.get("license") == "Apache-2.0" and (ROOT / "LICENSE").is_file(),
            str(manifest.get("license")),
        ),
        Check(
            "repository",
            str(manifest.get("repository_url", "")).rstrip("/") + ".git" == remote.rstrip("/"),
            remote,
        ),
        Check(
            "live demo",
            str(manifest.get("live_demo_url", "")).startswith("https://"),
            str(manifest.get("live_demo_url")),
        ),
        Check(
            "merged contribution",
            contribution.get("status") == "merged"
            and str(contribution.get("url", "")).startswith(
                "https://github.com/datahub-project/datahub/pull/"
            ),
            str(contribution.get("url")),
        ),
        Check("video file", video_path.is_file(), str(video_path.relative_to(ROOT))),
        Check(
            "video duration",
            float(receipt.get("duration_seconds", 999)) < 180,
            f"{receipt.get('duration_seconds')}s / 180s",
        ),
        Check("video scenes", receipt.get("scene_count") == 11, str(receipt.get("scene_count"))),
        Check(
            "video bytes",
            video_path.is_file() and receipt.get("bytes") == video_path.stat().st_size,
            str(receipt.get("bytes")),
        ),
        Check(
            "video digest",
            video_path.is_file() and receipt.get("sha256") == _sha256(video_path),
            str(receipt.get("sha256")),
        ),
        Check(
            "public video" if not allow_pending_video else "public video (preview bypass)",
            allow_pending_video
            or (
                receipt.get("public_upload_status") == "complete"
                and public_host in PUBLIC_VIDEO_HOSTS
            ),
            str(
                public_url
                or (
                    "BYPASSED: authenticated YouTube/Vimeo upload remains pending"
                    if allow_pending_video
                    else "PENDING: authenticated YouTube/Vimeo upload is required"
                )
            ),
        ),
        Check("clean worktree", not _git("status", "--porcelain"), head[:12]),
    ]

    if not online:
        return checks

    try:
        github = _json_url("https://api.github.com/repos/usv240/mosaic-datahub/commits/master")
        public_sha = str(github.get("sha", ""))
        checks.append(
            Check(
                "GitHub revision",
                public_sha == head,
                f"public={public_sha[:12]} local={head[:12]}",
            )
        )
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        checks.append(Check("GitHub revision", False, f"unverified: {type(error).__name__}"))

    try:
        deployment = _json_url(str(manifest["live_demo_url"]).rstrip("/") + "/api/deployment")
        deployed_sha = str(deployment.get("commit_sha", ""))
        checks.append(
            Check(
                "Railway revision",
                deployed_sha == head,
                f"deployed={deployed_sha[:12] or 'unknown'} local={head[:12]}",
            )
        )
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        checks.append(Check("Railway revision", False, f"unverified: {type(error).__name__}"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed Mosaic submission receipt audit.")
    parser.add_argument(
        "--online",
        action="store_true",
        help="also verify GitHub and Railway revisions",
    )
    parser.add_argument(
        "--allow-pending-video",
        action="store_true",
        help="preview mode only; public judging still requires a URL",
    )
    args = parser.parse_args()
    checks = audit(
        online=args.online,
        allow_pending_video=args.allow_pending_video,
    )
    for check in checks:
        print(f"{'PASS' if check.passed else 'FAIL'}  {check.name}: {check.detail}")
    failed = [check for check in checks if not check.passed]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("NOT SUBMISSION READY: " + ", ".join(check.name for check in failed))
        return 1
    if args.allow_pending_video:
        print("PREVIEW READY: public video is bypassed; final submission is not ready")
    else:
        print("SUBMISSION READY: every required receipt is present and current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
