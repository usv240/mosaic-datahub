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


def _finish_selected_case(page: Page, start_selector: str, *, pause_ms: int = 75) -> None:
    page.locator(start_selector).click()
    for _ in range(5):
        if pause_ms:
            page.wait_for_timeout(pause_ms)
        page.locator("#advance-demo-step").click(timeout=5_000)
    page.locator("#narrator.is-complete").wait_for(timeout=5_000)


def _complete_case_explorer(page: Page) -> None:
    page.locator("#run-all-scenarios").click()
    for index, name in enumerate(("research", "mitigated", "control", "audience")):
        if index:
            page.locator("#next-tour-case").click()
        _finish_selected_case(page, "#run-tour-case")
        page.wait_for_timeout(100)
        result_class = page.locator(f"[data-tour-result='{name}']").get_attribute("class")
        if not result_class or "is-verified" not in result_class:
            raise RuntimeError(f"{name} did not reach verified state")
    page.locator("#compare-tour").click()
    page.locator("#tour-summary").wait_for(state="visible", timeout=5_000)


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
        desktop.locator(".standards-section").evaluate(
            "element => { element.closest('details').open = true; }"
        )
        standards = desktop.locator(".standards-section")
        standards.scroll_into_view_if_needed()
        desktop.wait_for_timeout(500)
        standards_path = OUTPUT / "10-research-standards.png"
        standards.screenshot(path=standards_path)
        files.append(standards_path)
        desktop.locator(".agent-proof").evaluate(
            "element => { element.closest('details').open = true; }"
        )
        agent_proof = desktop.locator(".agent-proof")
        agent_proof.scroll_into_view_if_needed()
        desktop.wait_for_timeout(500)
        agent_path = OUTPUT / "11-agent-policy-boundary.png"
        agent_proof.screenshot(path=agent_path)
        files.append(agent_path)
        desktop.locator('[data-scenario="audience"]').click()
        desktop.wait_for_timeout(600)
        files.append(_screenshot(desktop, "02-audience-preset.png"))
        _finish_selected_case(desktop, "#run-demo")
        desktop.locator('[data-tab="attack"]').click()
        desktop.locator("#attack-verdict").filter(has_text="REFUSED").wait_for()
        attack_path = OUTPUT / "12-attack-refusal.png"
        desktop.locator("#tab-attack").screenshot(path=attack_path)
        files.append(attack_path)
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

        tour = browser.new_page(viewport={"width": 1440, "height": 1000})
        tour.emulate_media(reduced_motion="reduce")
        _ready(tour)
        _complete_case_explorer(tour)
        tour_path = OUTPUT / "13-four-case-scorecard.png"
        tour.locator("#tour-summary").screenshot(path=tour_path)
        files.append(tour_path)
        tour.close()

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

        # Narrated-video scenes are viewport captures, not unreadable full-page thumbnails.
        scenes = browser.new_page(viewport={"width": 1280, "height": 720})
        scenes.emulate_media(reduced_motion="reduce")

        def capture_scene(name: str) -> None:
            path = OUTPUT / name
            scenes.wait_for_timeout(250)
            scenes.screenshot(path=path)
            files.append(path)

        _ready(scenes)
        capture_scene("video-01-hero.png")

        scenes.locator('[data-scenario="research"]').click()
        _finish_selected_case(scenes, "#run-demo")
        scenes.locator("#workspace").scroll_into_view_if_needed()
        capture_scene("video-02-lineage.png")

        _ready(scenes)
        _complete_case_explorer(scenes)
        capture_scene("video-03-four-decisions.png")

        _ready(scenes)
        scenes.locator("#cross-asset-title").evaluate(
            "element => { element.closest('details').open = true; }"
        )
        scenes.locator(".cross-asset-proof").scroll_into_view_if_needed()
        capture_scene("video-04-cross-asset.png")

        scenes.locator('[data-scenario="research"]').click()
        _finish_selected_case(scenes, "#run-demo")
        scenes.locator("#workspace").scroll_into_view_if_needed()
        capture_scene("video-05-measured-result.png")

        scenes.locator(".agent-proof").evaluate(
            "element => { element.closest('details').open = true; }"
        )
        scenes.locator(".agent-proof").scroll_into_view_if_needed()
        capture_scene("video-06-agent-boundary.png")

        scenes.locator("#review-attack").click()
        scenes.locator("#attack-verdict").filter(has_text="REFUSED").wait_for(timeout=5_000)
        scenes.locator("#tab-attack").scroll_into_view_if_needed()
        capture_scene("video-07-attack-refusal.png")

        scenes.locator("#tab-button-codegen").click()
        scenes.locator("#generated-file-list .generated-file").first.wait_for()
        scenes.locator("#tab-codegen").scroll_into_view_if_needed()
        capture_scene("video-08-generated-pr.png")

        _ready(scenes)
        scenes.locator("#datahub-stack").scroll_into_view_if_needed()
        capture_scene("video-09-datahub-stack.png")

        _ready(scenes, "/runs")
        scenes.locator("#proof-catalog").scroll_into_view_if_needed()
        capture_scene("video-10-external-evidence.png")

        _ready(scenes, "/settings#readiness")
        scenes.locator("#connector-matrix").scroll_into_view_if_needed()
        capture_scene("video-11-production-readiness.png")
        scenes.close()

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
        _finish_selected_case(walkthrough, "#run-demo", pause_ms=650)
        for tab in ("query", "mitigation", "codegen", "writeback"):
            walkthrough.locator(f'[data-tab="{tab}"]').click()
            walkthrough.wait_for_timeout(1_000)
        walkthrough.locator("#cross-asset-title").evaluate(
            "element => { element.closest('details').open = true; }"
        )
        walkthrough.locator("#cross-asset-title").scroll_into_view_if_needed()
        walkthrough.wait_for_timeout(1_200)
        walkthrough.locator("#agent-proof-title").scroll_into_view_if_needed()
        walkthrough.wait_for_timeout(1_500)
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
