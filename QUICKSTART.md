# Mosaic judge quickstart

## Fast offline review

```powershell
uv sync --extra dev
uv run mosaic demo
uv run pytest
uv run mosaic serve
```

Open `http://127.0.0.1:8123`. The console uses a frozen synthetic estate and needs no
network, LLM, warehouse, or DataHub service. The demo intentionally exits `3`: the
fixture contains a validated critical risk, so a reviewer should block its release.

## Live DataHub proof

Start a local DataHub Core instance at `http://localhost:8080`, then install optional
DataHub dependencies and run:

```powershell
uv sync --extra datahub --extra dev
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

It creates uniquely named synthetic assets, then proves:

1. schema and fine-grained lineage are re-readable from DataHub Core;
2. the approved `GROUP BY COUNT(*)` query executes in isolated DuckDB;
3. zero raw rows are returned to Mosaic; and
4. an explicitly approved tag and threat-model Document are written to, then reread
   from, DataHub.

Do not point the probe at a production catalog: it deliberately creates synthetic
assets and metadata to demonstrate the integration.
