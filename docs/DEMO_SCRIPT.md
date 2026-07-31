# Mosaic demo — 2:50 target

## 0:00–0:20 — The claim

Open at the top of the landing page: “Three ordinary columns, three systems, one export. No field is direct PII. DataHub’s graph shows why the combination matters.” Define minimum k in one sentence: the size of the smallest crowd a record blends into; k=1 is unique.

## 0:20–0:48 — Challenge a catalog Mosaic did not create

Run `mosaic discover` against DataHub's official showcase `order_details` asset. Point to 55 inspected fields, three classified families, 10 true upstream datasets, dataset-only column origins, and zero raw rows. Then show the single-source `order_items` control returning `no_convergence`. Say: “Same reader, opposite result. Mosaic excludes job nodes and refuses to invent a graph finding.”

## 0:48–1:05 — The model proposes; policy disposes

Open `/api/agent-receipts`. Show the real local Mistral proposal that nominated an asset and columns, followed by Mosaic's deterministic query and critical verdict. Then show the preserved veto receipt. Say: “The model writes rationale, never SQL. Policy owns the query, verdict, execution boundary, and veto.”
## 1:05–1:30 — Measured evidence

Run the research investigation. Show k=1, 100% below k=5, zero raw person-level rows, and three downstream assets. Open the false-positive rebuttal: ordinary fields and high cardinality alone are insufficient; independent lineage convergence plus measured small classes earns the critical verdict.

## 1:30–2:05 — Generated PR bundle

Open Remediation PR and click the six files: dbt model, enforced typed contract, aggregate-only test, organization-policy snapshot, provenance manifest, and PR summary. Show DataHub URN, policy/scenario digests, Snowflake-ready adapter boundary, and human-review gate. Download the reproducible ZIP.

## 2:05–2:35 — Write back, then re-read

Show the DataHub proposal. Approve only in disposable local DataHub. Re-read the field tag, structured property, threat-model Document, and active incident. State: “The decision survives for the next human or agent.” Mention the merged upstream DataHub contribution.

## 2:35–2:50 — Limits and close

Say this out loud: “This is privacy risk reduction, not proof of anonymity or legal compliance. Production needs organization policy owners, scoped DataHub and warehouse identities, SSO/RBAC, and compatibility validation.” Close: “Mosaic turns hidden graph context into code a data team can review before risk spreads.”

## Backup judge commands

```powershell
uv sync --locked --extra dev
uv run mosaic discover --server http://localhost:8080 --urn "<existing-sample-urn>"
uv run mosaic assess --scenario research
uv run mosaic check --fail-on critical
uv run mosaic benchmark
uv run mosaic replay-fixture
uv run mosaic generate-remediation --scenario research --output generated/research
uv run mosaic serve
```

Critical assessment, estate scan, and pre-merge gate intentionally return exit code 3. That is a policy result, not an application crash.