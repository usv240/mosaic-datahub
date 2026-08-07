from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mosaic.adoption import adoption_catalog
from mosaic.datahub_graphql import graphql
from mosaic.engine import run_judge_demo
from mosaic.estate_scan import scan_estate
from mosaic.governed_writeback import publish
from mosaic.mitigation_lab import compare_mitigations
from mosaic.proof_catalog import proof_catalog
from mosaic.remediation_codegen import generate_remediation_bundle, remediation_zip
from mosaic.runs import list_runs, load_run, record
from mosaic.scenario_registry import assess_scenario, list_scenarios
from mosaic.technology import technology_catalog

WEB_ROOT = Path(__file__).parent


class PublishRequest(BaseModel):
    csrf_token: str
    confirmation: str


def _is_public() -> bool:
    return os.getenv("MOSAIC_PUBLIC_DEMO", "").lower() in {"1", "true", "yes"}


def _writeback_enabled() -> bool:
    return os.getenv("MOSAIC_ENABLE_WEB_WRITEBACK", "").lower() in {"1", "true", "yes"}


def create_app(project_root: Path | None = None) -> FastAPI:
    root = project_root or Path.cwd()
    runs_dir = root / "runs"
    app = FastAPI(title="Mosaic Privacy Console", version="0.2.0")
    app.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; object-src 'none'; "
            "frame-ancestors 'none'; form-action 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'"
        )
        # Scripts and markup ship together and are versioned only by deploy. Without an
        # explicit directive a browser caches them heuristically, so a visitor who saw an
        # earlier deploy can run stale JavaScript against current markup — the controls
        # then silently no-op. Revalidate every time; ETags keep the cost to a 304.
        if request.url.path.startswith("/static/") or response.headers.get(
            "content-type", ""
        ).startswith("text/html"):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/deployment")
    def deployment() -> dict[str, str]:
        return {
            "status": "ok",
            "commit_sha": os.getenv(
                "RAILWAY_GIT_COMMIT_SHA",
                os.getenv("MOSAIC_BUILD_SHA", "development"),
            ),
            "environment": os.getenv("RAILWAY_ENVIRONMENT_NAME", "local"),
        }

    @app.get("/api/health/datahub")
    def datahub_health(probe: bool = False) -> dict[str, object]:
        server = os.getenv("MOSAIC_DATAHUB_URL", "http://localhost:8080")
        result: dict[str, object] = {
            "status": "not_probed",
            "server": server,
            "public_demo": _is_public(),
            "web_writeback_enabled": _writeback_enabled() and not _is_public(),
        }
        if not probe:
            return result
        try:
            graphql(server, "query MosaicHealth { __typename }", {})
        except Exception:
            result["status"] = "unavailable"
        else:
            result["status"] = "connected"
        return result

    @app.get("/api/approval-token")
    def approval_token(response: Response) -> dict[str, object]:
        if _is_public() or not _writeback_enabled():
            raise HTTPException(status_code=403, detail="Browser write-back is disabled.")
        token = secrets.token_urlsafe(32)
        response.set_cookie("mosaic_csrf", token, httponly=False, samesite="strict")
        return {"csrf_token": token, "confirmation_required": "PUBLISH SYNTHETIC EVIDENCE"}

    @app.post("/api/publish")
    def publish_from_browser(payload: PublishRequest, request: Request) -> dict[str, object]:
        if _is_public() or not _writeback_enabled():
            raise HTTPException(status_code=403, detail="Browser write-back is disabled.")
        cookie = request.cookies.get("mosaic_csrf")
        if not cookie or not secrets.compare_digest(cookie, payload.csrf_token):
            raise HTTPException(status_code=403, detail="Invalid approval token.")
        if payload.confirmation != "PUBLISH SYNTHETIC EVIDENCE":
            raise HTTPException(status_code=400, detail="Exact confirmation phrase required.")
        server = os.getenv("MOSAIC_DATAHUB_URL", "http://localhost:8080")
        return publish(server, approved=True)

    @app.get("/api/technology")
    def technology() -> dict[str, object]:
        return technology_catalog()

    @app.get("/api/adoption")
    def adoption() -> dict[str, object]:
        return adoption_catalog()

    @app.get("/api/assessment")
    def assessment() -> dict[str, object]:
        return run_judge_demo()

    @app.get("/api/mitigations")
    def mitigations() -> dict[str, object]:
        return compare_mitigations()

    @app.get("/api/remediation-bundles/{slug}")
    def remediation_bundle(slug: str) -> dict[str, object]:
        try:
            return generate_remediation_bundle(slug)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown Mosaic scenario") from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/api/remediation-bundles/{slug}/download")
    def remediation_download(slug: str) -> Response:
        try:
            content = remediation_zip(slug)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown Mosaic scenario") from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return Response(
            content=content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="mosaic-{slug}-remediation.zip"',
                "Cache-Control": "no-store",
            },
        )

    @app.get("/api/scenarios")
    def scenarios() -> dict[str, object]:
        return {
            "scenarios": [
                {
                    "slug": item.slug,
                    "name": item.name,
                    "domain": item.domain,
                    "situation": item.situation,
                    "configuration_sha256": item.config_sha256,
                }
                for item in list_scenarios()
            ]
        }

    @app.get("/api/scenarios/{slug}")
    def scenario_assessment(slug: str) -> dict[str, object]:
        try:
            return assess_scenario(slug)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown Mosaic scenario") from error

    @app.get("/api/scan")
    def estate_scan() -> dict[str, object]:
        return scan_estate()

    @app.get("/api/agent-receipts")
    def agent_receipts() -> dict[str, object]:
        receipt_root = root / "evidence" / "external"
        names = ("ollama-agent-accepted-live.json", "ollama-agent-veto-live.json")
        receipts = []
        for name in names:
            path = receipt_root / name
            if path.is_file():
                try:
                    receipts.append(json.loads(path.read_text(encoding="utf-8")))
                except json.JSONDecodeError as error:
                    raise HTTPException(
                        status_code=503, detail="Agent receipt is malformed"
                    ) from error
        if not receipts:
            raise HTTPException(status_code=404, detail="No local-model receipt is packaged")
        return {
            "schema_version": 1,
            "execution_boundary": "recorded local Ollama runs; hosted page performs no inference",
            "receipts": receipts,
        }

    @app.get("/api/redteam")
    def redteam_receipt() -> dict[str, object]:
        from mosaic.redteam import run_redteam

        transcript = root / "fixtures" / "agent_transcripts" / "prompt-injection.json"
        try:
            return run_redteam(transcript)
        except ValueError as error:
            raise HTTPException(
                status_code=503, detail="Red-team receipt is unavailable"
            ) from error

    @app.get("/api/proofs")
    def proofs() -> dict[str, object]:
        return proof_catalog(root)

    @app.post("/api/runs")
    def create_run(scenario: str = "research") -> dict[str, object]:
        if _is_public():
            raise HTTPException(
                status_code=403,
                detail="The hosted demo is read-only; run Mosaic locally to retain evidence.",
            )
        try:
            bundle = assess_scenario(scenario)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown Mosaic scenario") from error
        return record(bundle, runs_dir)

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

    @app.get("/api/runs/{run_id}")
    def run_detail_api(run_id: str) -> dict[str, object]:
        try:
            return load_run(runs_dir, run_id)
        except (FileNotFoundError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="Evidence run not found") from None

    @app.get("/", response_class=HTMLResponse)
    def overview() -> HTMLResponse:
        return HTMLResponse((WEB_ROOT / "experience.html").read_text(encoding="utf-8"))

    @app.get("/runs", response_class=HTMLResponse)
    def run_history() -> HTMLResponse:
        return HTMLResponse((WEB_ROOT / "runs_experience.html").read_text(encoding="utf-8"))

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_detail(run_id: str) -> HTMLResponse:
        try:
            load_run(runs_dir, run_id)
        except (FileNotFoundError, json.JSONDecodeError):
            raise HTTPException(status_code=404, detail="Evidence run not found") from None
        return HTMLResponse((WEB_ROOT / "run_detail.html").read_text(encoding="utf-8"))

    @app.get("/settings", response_class=HTMLResponse)
    def settings() -> HTMLResponse:
        return HTMLResponse((WEB_ROOT / "settings.html").read_text(encoding="utf-8"))

    return app
