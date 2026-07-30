# Mosaic demo — 2:50 target

## 0:00–0:20 — The claim

Open at the top of the landing page: “Three ordinary columns, three systems, one export. No field is direct PII. DataHub’s graph shows why the combination matters.” Define minimum k in one sentence: the size of the smallest crowd a record blends into; k=1 is unique.

## 0:20–0:45 — Read a catalog Mosaic did not create

Run `mosaic discover` against an existing DataHub quickstart sample URN. Keep the tool output visible. Point to schema, glossary/tag evidence, column lineage, and distinct upstream datasets. Run the single-source control and show `no_convergence`. Say: “Mosaic does not need to seed this asset, and it refuses to invent a graph finding.”

## 0:45–1:05 — The model proposes; policy disposes

Show an agent-proposed query containing `member_id`. Let the query policy reject it. Then show the approved aggregate-only `GROUP BY COUNT(*)` shape. This is the architecture: an agent can propose; deterministic policy owns data access and the verdict.

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