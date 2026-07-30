from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = os.getenv("MOSAIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
OUTPUT = Path(os.getenv("MOSAIC_MEDIA_DIR", "artifacts/submission-media"))


def _ready(page: Page, path: str = "/") -> None:
    page.goto(BASE + path, wait_until="networkidle", timeout=40_000)
    page.wait_for_timeout(350)


def _screenshot(page: Page, name: str, *, full_page: bool = True) -> Path:
    path = OUTPUT / name
    page.screenshot(path=path, full_page=full_page)
    return path


def main() -> int:
    started = time.monotonic()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    video_dir = OUTPUT / "raw-video"
    video_dir.mkdir(exist_ok=True)
    files: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        desktop = browser.new_page(viewport={"width": 1440, "height": 1000})
        _ready(desktop)
        desktop.evaluate("localStorage.setItem('mosaic-theme', 'dark')")
        _ready(desktop)
        files.append(_screenshot(desktop, "01-landing-dark.png"))
        architecture = desktop.locator("#datahub-stack")
        architecture.scroll_into_view_if_needed()
        desktop.wait_for_timeout(500)
        architecture_path = OUTPUT / "08-datahub-architecture.png"
        architecture.screenshot(path=architecture_path)
        files.append(architecture_path)
        standards = desktop.locator(".standards-section")
        standards.scroll_into_view_if_needed()
        desktop.wait_for_timeout(500)
        standards_path = OUTPUT / "10-research-standards.png"
        standards.screenshot(path=standards_path)
        files.append(standards_path)
        desktop.locator('[data-scenario="audience"]').click()
        desktop.wait_for_timeout(600)
        files.append(_screenshot(desktop, "02-audience-preset.png"))
        desktop.locator("#run-demo").click()
        desktop.wait_for_timeout(3_800)
        desktop.locator('[data-tab="mitigation"]').click()
        files.append(_screenshot(desktop, "03-completed-investigation.png"))
        desktop.locator('[data-tab="codegen"]').click()
        desktop.locator("#generated-file-list .generated-file").first.wait_for()
        codegen_path = OUTPUT / "09-remediation-pr.png"
        desktop.locator("#tab-codegen").screenshot(path=codegen_path)
        files.append(codegen_path)
        _ready(desktop, "/runs")
        files.append(_screenshot(desktop, "04-evidence-catalog.png"))
        _ready(desktop, "/settings")
        desktop.locator("#connector-matrix[data-has-integration-boundary='true']").wait_for()
        files.append(_screenshot(desktop, "05-operator-safety.png"))
        desktop.close()

        light = browser.new_page(viewport={"width": 1440, "height": 1000})
        _ready(light)
        light.evaluate("localStorage.setItem('mosaic-theme', 'light')")
        _ready(light)
        files.append(_screenshot(light, "06-landing-light.png"))
        light.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        _ready(mobile)
        files.append(_screenshot(mobile, "07-mobile-landing.png"))
        mobile.close()

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=video_dir,
            record_video_size={"width": 1440, "height": 900},
        )
        walkthrough = context.new_page()
        _ready(walkthrough)
        walkthrough.mouse.wheel(0, 650)
        walkthrough.wait_for_timeout(1_000)
        walkthrough.locator('[data-scenario="audience"]').click()
        walkthrough.wait_for_timeout(1_000)
        walkthrough.locator('[data-scenario="research"]').click()
        walkthrough.wait_for_timeout(800)
        walkthrough.locator("#run-demo").click()
        walkthrough.wait_for_timeout(4_000)
        for tab in ("query", "mitigation", "codegen", "writeback"):
            walkthrough.locator(f'[data-tab="{tab}"]').click()
            walkthrough.wait_for_timeout(1_000)
        _ready(walkthrough, "/runs")
        walkthrough.mouse.wheel(0, 850)
        walkthrough.wait_for_timeout(1_500)
        _ready(walkthrough, "/settings")
        walkthrough.wait_for_timeout(1_500)
        context.close()
        videos = sorted(video_dir.glob("*.webm"))
        if len(videos) != 1:
            raise RuntimeError(f"expected one recorded walkthrough, found {len(videos)}")
        final_video = OUTPUT / "08-product-walkthrough.webm"
        videos[0].replace(final_video)
        video_dir.rmdir()
        files.append(final_video)
        browser.close()

    manifest = {
        "schema_version": 1,
        "captured_at": datetime.now(UTC).isoformat(),
        "base_url": BASE,
        "purpose": "Judge screenshots and edit-ready product footage generated from the running Mosaic application.",
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in files
        ],
        "video_duration_limit_seconds": 180,
        "note": "The WebM is captioned by the product UI but requires narration and public YouTube/Vimeo upload for Devpost.",
    }
    manifest_path = OUTPUT / "media-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Captured {len(files)} media files at {OUTPUT} in {time.monotonic() - started:.3f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
