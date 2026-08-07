"""Prove the in-browser measurement matches the Python engine and uploads nothing.

The bring-your-own-data widget reimplements the anonymity computation in
JavaScript so a visitor's file never leaves their machine. Two things can go
wrong with that: the two engines can drift, and a future edit could start
posting the file somewhere. This check drives the real widget in a real browser
and fails on either.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from mosaic.measure import measure_file

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "examples" / "bring-your-own-data"
HOST, PORT = "127.0.0.1", 8231
CASES = (
    ("risky_member_export.csv", ("zip5", "birth_date", "gender"), "CRITICAL"),
    ("safe_member_export.csv", ("region", "age_band", "gender"), "CLEAR"),
    ("borderline_partner_audience.csv", ("region", "age_band", "device_type"), "ELEVATED"),
)


def _serve() -> subprocess.Popen[bytes]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mosaic.web.complete_app:create_app",
            "--factory",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(6)
    return process


def main() -> int:
    server = _serve()
    failures: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            posted: list[str] = []
            page.on(
                "request",
                lambda request: (
                    posted.append(request.url)
                    if request.method in {"POST", "PUT", "PATCH"}
                    else None
                ),
            )
            for name, columns, expected in CASES:
                page.goto(f"http://{HOST}:{PORT}/", wait_until="networkidle", timeout=40_000)
                page.wait_for_timeout(400)
                page.locator("#byod-file").set_input_files(str(SAMPLES / name))
                page.wait_for_timeout(700)
                for column in columns:
                    page.locator(f'#byod-columns input[value="{column}"]').check()
                page.locator("#byod-run").click()
                page.wait_for_timeout(400)
                engine = measure_file(SAMPLES / name, columns)["metrics"]
                shown = {
                    "verdict": page.locator("#byod-verdict").inner_text().strip(),
                    "records": int(page.locator("#byod-records").inner_text()),
                    "combinations": int(page.locator("#byod-combos").inner_text()),
                    "minimum_k": int(page.locator("#byod-k").inner_text()),
                    "below5": float(page.locator("#byod-below").inner_text().rstrip("%")),
                }
                if shown["verdict"] != expected:
                    failures.append(f"{name}: verdict {shown['verdict']} != {expected}")
                if shown["records"] != engine["total_records"]:
                    failures.append(
                        f"{name}: records {shown['records']} != {engine['total_records']}"
                    )
                if shown["combinations"] != engine["distinct_combinations"]:
                    failures.append(f"{name}: combinations disagree with the Python engine")
                if shown["minimum_k"] != engine["minimum_k"]:
                    failures.append(
                        f"{name}: minimum_k {shown['minimum_k']} != {engine['minimum_k']}"
                    )
                if abs(shown["below5"] - engine["percent_below_5"]) > 0.001:
                    failures.append(f"{name}: percent_below_5 disagrees with the Python engine")
            if posted:
                failures.append(f"the page issued {len(posted)} write request(s): {posted}")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=20)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(
        f"Browser measurement matches the Python engine on {len(CASES)} samples; "
        "no file content was transmitted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
