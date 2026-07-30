# Mosaic quick start

## Fastest judge path

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

Open `http://127.0.0.1:8123`, select a preset, and choose **Run guided analysis**. No network, LLM, warehouse, Docker, or DataHub instance is required.

## Verify the central claims

```powershell
uv run mosaic assess --scenario research
uv run mosaic assess --scenario mitigated
uv run mosaic assess --scenario control
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
```

`research` and the estate scan return exit code 3 because they contain a validated critical finding. `mitigated`, `control`, `benchmark`, and `replay-fixture` return zero.

## Retain inspectable evidence

The local console can create a digest-backed scenario run. Open **Evidence**, choose **Inspect evidence**, verify its SHA-256 status, and print or save the human-readable report as PDF. The public deployment intentionally refuses this filesystem write.

## Optional live DataHub proof

Use only a disposable local catalog:

```powershell
uv sync --locked --extra dev --extra datahub
uv run mosaic live-demo --server http://localhost:8080
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

The first run produces a proposal. The approved run creates uniquely named synthetic evidence, then re-reads each mutation. To use the browser approval UI, set `MOSAIC_ENABLE_WEB_WRITEBACK=true` and `MOSAIC_DATAHUB_URL=http://localhost:8080` before starting the server; the hosted demo remains read-only.

## Full verification

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=mosaic --cov-report=term-missing --cov-fail-under=99
uv build
uv run python scripts/check_cli_contracts.py
uv run python scripts/check_json_deliverables.py
uv run python scripts/check_utf8.py
```