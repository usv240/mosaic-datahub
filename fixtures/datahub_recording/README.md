# Recorded DataHub metadata fixture

This fixture is a sanitized semantic recording of Mosaic's verified synthetic DataHub Core run.
It contains catalog metadata and reread results only. It contains no person-level rows.

The manifest pins the DataHub surfaces used during capture and hashes every response. Run:

```bash
uv run mosaic replay-fixture
```

The replay fails if any response changes or if the recorded schema, lineage, blast radius,
write-back, MCP, or zero-row contracts no longer agree.

This fixture proves deterministic replay of a previously verified integration. It does not claim
that a live DataHub instance is available on the public host.
