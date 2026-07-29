# Live DataHub evidence

Run from an environment with the optional DataHub dependencies installed:

```powershell
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

The command creates uniquely named synthetic Mosaic datasets, proves column-level
lineage is readable from DataHub Core, executes the approved count-only aggregate in
DuckDB, then performs an approved tag/document write-back and re-reads both artifacts.
The generated `live.local.json` is intentionally ignored because its unique asset URNs
and timestamp are environment-specific.
