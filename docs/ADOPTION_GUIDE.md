# Adopt Mosaic

Mosaic has four deliberately separate adoption stages. A new visitor can understand the product without credentials; a production operator must supply organization-specific controls. The project does not blur those states.

## 1. Explore — no setup

Open the [read-only hosted demo](https://mosaic-datahub-production.up.railway.app), choose any of the four cases, and run the guided investigation. The demo serves deterministic engine evidence, returns no person-level rows, and rejects mutations.

Use this stage to answer:

- Is compositional privacy risk relevant to our data-sharing workflows?
- Can privacy, data, governance, and security teams understand the same finding?
- Does the aggregate-only safety boundary meet our evaluation expectations?

## 2. Evaluate — local and reproducible

### Python

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

### Container

```powershell
docker compose up --build
```

Open `http://127.0.0.1:8123`. The Compose path intentionally starts in public-demo mode, so it is read-only even on a developer laptop.

Reproduce the non-browser evidence:

```powershell
uv run mosaic assess --scenario research
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
```

The critical assessment and scan return exit code `3`; that is a policy result, not a process crash.

## 3. Connect — disposable DataHub Core

Install the DataHub integration extras and point Mosaic at a non-production DataHub environment:

```powershell
uv sync --locked --extra dev --extra datahub
uv run mosaic live-demo --server http://localhost:8080
```

The command creates uniquely named synthetic assets and remains dry-run by default. It verifies schema, fine-grained lineage, downstream impact, GraphQL, MCP, and the governance proposal without changing a real business dataset.

Only use the approved variant after reviewing the synthetic target:

```powershell
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

The approved workflow re-reads the field tag, structured property, threat-model Document, and incident after publication.

## 4. Operate — organization controls required

Before applying Mosaic to a real estate, provide all of the following:

1. An authenticated DataHub service identity with least-privilege metadata access.
2. An organization-approved aggregate query adapter for each warehouse in scope.
3. Explicit asset and column allowlists; do not grant estate-wide query access by default.
4. Privacy-owned anonymity thresholds and exception policy.
5. SSO, RBAC, secret management, audit retention, and network controls.
6. Named reviewers who own approval and remediation decisions.
7. A compatibility run against the deployed DataHub and warehouse versions.

Mosaic currently implements DataHub Core integration and DuckDB reference validation. Snowflake, BigQuery, Databricks, Postgres, and enterprise identity systems are integration boundaries, not claimed built-in connectors.

## Environment contract

Copy `.env.example` and keep the safe defaults until a local review explicitly changes them.

| Variable | Safe default | Purpose |
|---|---|---|
| `MOSAIC_PUBLIC_DEMO` | `true` | Forces hosted read-only behavior and blocks retained runs and publication. |
| `MOSAIC_DATAHUB_URL` | `http://localhost:8080` | Selects the DataHub Core endpoint used by health and publication workflows. |
| `MOSAIC_ENABLE_WEB_WRITEBACK` | `false` | Enables the local browser approval flow; ignored whenever public-demo mode is on. |

## Warehouse adapter safety contract

Any production warehouse integration must preserve the existing query boundary:

- one allowlisted table;
- allowlisted quasi-identifier columns;
- `COUNT(*)` grouped by those columns;
- no joins, filters, mutations, additional statements, or person-level projection;
- a recorded raw-row count of zero;
- a fail-closed response when validation or authorization is uncertain.

This contract is more important than supporting a long connector list. A connector that weakens it should not be shipped.

