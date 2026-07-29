from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from mosaic.engine import run_judge_demo
from mosaic.mitigation_lab import compare_mitigations
from mosaic.runs import list_runs, record

WEB_ROOT = Path(__file__).parent


def create_app(project_root: Path | None = None) -> FastAPI:
    root = project_root or Path.cwd()
    runs_dir = root / "runs"
    app = FastAPI(title="Mosaic Privacy Console", version="0.2.0")
    app.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/assessment")
    def assessment() -> dict[str, object]:
        return run_judge_demo()

    @app.get("/api/mitigations")
    def mitigations() -> dict[str, object]:
        return compare_mitigations()

    @app.post("/api/runs")
    def create_run() -> dict[str, object]:
        if os.getenv("MOSAIC_PUBLIC_DEMO", "").lower() in {"1", "true", "yes"}:
            raise HTTPException(
                status_code=403,
                detail="The hosted demo is read-only; run Mosaic locally to retain evidence.",
            )
        return record(run_judge_demo(), runs_dir)

    @app.get("/api/runs")
    def runs() -> dict[str, object]:
        return {"runs": list_runs(runs_dir)}

    @app.get("/api/runs/{run_id}/evidence.json")
    def evidence(run_id: str) -> FileResponse:
        if not run_id.startswith("mosaic-") or any(char in run_id for char in ("/", "\\", "..")):
            raise HTTPException(status_code=404)
        path = runs_dir / f"{run_id}.json"
        if not path.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(path, media_type="application/json", filename=f"{run_id}.json")

    @app.get("/", response_class=HTMLResponse)
    def overview() -> HTMLResponse:
        return HTMLResponse((WEB_ROOT / "index.html").read_text(encoding="utf-8"))

    @app.get("/runs", response_class=HTMLResponse)
    def run_history() -> HTMLResponse:
        return HTMLResponse((WEB_ROOT / "runs.html").read_text(encoding="utf-8"))

    return app
