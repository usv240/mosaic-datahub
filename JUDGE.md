# Judge path

The complete application is reproducible in Mosaic's own locked environment:

```powershell
uv sync --extra dev --extra datahub
uv run mosaic demo
uv run mosaic serve
```

Open `http://127.0.0.1:8123`. The console includes the assessment, interactive attack
path, light/dark themes, exact risk metrics, mitigation comparison API, retained run
history, and downloadable digest-backed evidence.

With local DataHub Core available at `http://localhost:8080`:

```powershell
uv run mosaic live-demo --approve-writeback
```

This creates only uniquely named synthetic assets. It verifies DataHub-discovered
convergence and downstream blast radius, exact aggregate execution in DuckDB, zero raw
rows, and approved tag/property/Document/incident persistence by rereading each.

Official MCP proof is in `mosaic.mcp_probe`; it verifies search, column lineage, tag
mutation, and reread through `mcp-server-datahub`. The installed Agent Context Kit can
resolve previously indexed dataset paths but did not reliably resolve freshly seeded
fine-grained edges during its bounded probe; Mosaic does not claim that check as passed.
