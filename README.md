# Mosaic

> No column here is PII. Together, they identify you.

**[Try the read-only live demo](https://mosaic-datahub-production.up.railway.app)**

**Challenge: Metadata-Aware Code Generation & Development**

Mosaic is a DataHub-grounded privacy remediation code-generation agent. It discovers ordinary attributes that become identifying only after pipelines bring them together, validates the combination with aggregate-only anonymity metrics, traces the downstream blast radius, compares mitigations, generates a merge-ready remediation bundle, and prepares governed catalog evidence for human approval.

A PII scanner classifies columns. Mosaic reasons over the graph.

## Potential impact

Mosaic moves privacy intervention upstream: before a research export, partner delivery, audience, or model dataset spreads a risky combination across the estate.

- **Prevent hidden exposure:** find re-identification risk that field-by-field classification cannot see.
- **Contain the blast radius:** prioritize every downstream consumer that inherited the combination.
- **Preserve useful data:** compare reversible mitigations instead of blocking an entire release.
- **Create institutional memory:** leave reviewed evidence, ownership, incidents, and decisions in DataHub.

The workflow gives privacy, data, governance, and security teams one explainable finding without exposing person-level rows. Real-world impact depends on approved access, organization-owned thresholds, and human review; Mosaic keeps that boundary visible.

## Understand it in 90 seconds

Imagine three source systems:

- a location service contributes ZIP5;
- a clinical system contributes birth date;
- an enrollment system contributes demographic category.

No field is a direct identifier. DataHub's fine-grained lineage reveals that all three arrive in the same research export. Mosaic then runs a narrowly allow-listed grouped count and asks: how many records share each combination? In the primary synthetic case the smallest group has one record (`k=1`) and every record is below `k=5`. No person-level row is returned.

The proposed shadow mitigation suppresses birth date, increasing the smallest group to twenty while preserving the source asset. Mosaic then generates a dbt model, schema contract, aggregate-only privacy test, policy file, provenance manifest, and PR summary. A reviewer can inspect every line before merge or DataHub write-back.

## Judge quick start

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

Open `http://127.0.0.1:8123`. The console includes light and dark modes, a narrated attack path, four backend scenarios, safe controls, exact metrics, a mitigation lab, retained evidence history, printable run reports, operator settings, and plain-English definitions.

Or start the safe, read-only container path:

```powershell
docker compose up --build
```

The core CLI is completely offline:

```powershell
uv run mosaic assess --scenario research
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
uv run mosaic generate-remediation --scenario research --output generated/research
```

With local DataHub Core running, execute the strongest end-to-end proof:

```powershell
uv run mosaic live-demo --server http://localhost:8080
```

That run seeds isolated SDK assets, reads fine-grained lineage and downstream impact from DataHub, carries the discovered schema and URNs into the six-file remediation bundle, compiles the generated SQL, and leaves write-back behind the human approval gate.

A validated critical result returns exit code `3`; this is the policy outcome, not a crash.

## What the agent does

1. Screens DataHub schemas, tags, fine-grained lineage, and downstream dependencies.
2. Requires credible convergence across multiple quasi-identifier families before querying data.
3. Builds and validates one aggregate-only `COUNT(*) ... GROUP BY` shape.
4. Measures minimum k and record percentages below k=2, k=5, and k=10.
5. Compares the lineage-aware finding with a no-lineage baseline.
6. Ranks estate findings by severity, anonymity, and downstream reach.
7. Compares generalization, suppression, access control, and purpose limitation.
8. Generates a dbt model, schema contract, aggregate-only test, policy, manifest, and PR summary.
9. Records digest-backed evidence and prepares DataHub governance context.
10. Publishes only after explicit approval, then re-reads every mutation.

## Remediation PR Studio

Mosaic turns a validated graph finding into code a data team can review and merge. Generation is deterministic, digest-backed, and grounded in the selected scenario's DataHub URN, fine-grained lineage, schema, and downstream impact.

| Generated artifact | Purpose |
|---|---|
| `models/*_privacy_safe.sql` | dbt model implementing the selected suppression or generalization |
| `models/*_privacy_safe.yml` | Column contract, DataHub URN, scenario digest, and before/after metrics |
| `tests/assert_*_minimum_k.sql` | Singular dbt test that returns only an aggregate failure metric |
| `.mosaic/privacy-policy.yml` | Review thresholds, required roles, and post-merge write-back plan |
| `mosaic-manifest.json` | DataHub context and SHA-256 digest for every generated artifact |
| `PR_SUMMARY.md` | Reviewer-ready rationale, lineage, blast radius, and approval checklist |

Inspect the committed [research](examples/generated/research-remediation) and [audience](examples/generated/audience-remediation) outputs, call `/api/remediation-bundles/{scenario}`, or download the reproducible ZIP from `/api/remediation-bundles/{scenario}/download`. A safe negative control produces no bundle; Mosaic refuses to manufacture unnecessary code.

## Evidence ladder

| Proof | Result | Honest scope |
|---|---:|---|
| Configured scenarios | 4 working backend cases across two domains | Deterministic product behavior |
| Generated remediation | 2 committed bundles; 6 artifacts each; hashes reproducible | Review-ready examples, not automatically merged code |
| Regression benchmark | 48 cases; exact agreement 100%; seeded precision/recall 100% | Deliberately bounded policy regression, not field accuracy |
| DataHub recording replay | Hashes and semantic checks pass | Versioned normalized integration semantics, not a live server |
| UCI Adult external proof | 32,561 rows processed in memory; k=43 to k=1 after composition; 23.786% below k=5 | Historical external mechanism check, not current prevalence |
| Live local DataHub workflow | Schema, lineage, downstream, generated six-file remediation, SQL compile, write-back, and re-read | Environment-specific proof when the operator runs it |

See [evaluations/benchmark.json](evaluations/benchmark.json), [fixtures/datahub_recording/manifest.json](fixtures/datahub_recording/manifest.json), and [evidence/external/uci-adult-proof.json](evidence/external/uci-adult-proof.json).

## Product tour

| First-visit education | Guided investigation |
|---|---|
| [![Mosaic landing page in dark mode](docs/screenshots/01-landing-dark.png)](docs/screenshots/01-landing-dark.png) | [![Completed privacy investigation](docs/screenshots/03-completed-investigation.png)](docs/screenshots/03-completed-investigation.png) |
| **Evidence catalog** | **Responsive light mode** |
| [![Reproducible proof catalog](docs/screenshots/04-evidence-catalog.png)](docs/screenshots/04-evidence-catalog.png) | [![Mosaic landing page in light mode](docs/screenshots/06-landing-light.png)](docs/screenshots/06-landing-light.png) |
| **Remediation PR Studio** | **DataHub architecture** |
| [![Generated remediation code review](docs/screenshots/09-remediation-pr.png)](docs/screenshots/09-remediation-pr.png) | [![DataHub technology architecture](docs/screenshots/08-datahub-architecture.png)](docs/screenshots/08-datahub-architecture.png) |

The repository also includes the complete [screenshot gallery](docs/screenshots/README.md) and an [edit-ready product walkthrough](docs/demo/08-product-walkthrough.webm). The walkthrough is source footage for the required narrated public submission video; it is not presented as the final YouTube/Vimeo entry.

## How Mosaic uses DataHub

**DataHub is the reasoning substrate, not a logo in the footer.** Without DataHub, Mosaic has isolated column names. With DataHub, it can reconstruct cross-source convergence, determine who inherited the risk, and leave a verified governance decision behind.

```text
DataHub schema + fine-grained lineage
                  |
                  v
      Mosaic graph-native reasoning
                  |
                  v
 DuckDB aggregate-only validation
                  |
                  v
      DataHub downstream blast radius
                  |
                  v
    merge-ready remediation bundle
                  |
                  v
 reviewed tag + property + Document + incident
```

| DataHub capability | What Mosaic does with it | Inspect the implementation |
|---|---|---|
| Fine-grained lineage | Reconstructs ordinary columns that originate separately and converge in one asset | [`live_estate.py`](src/mosaic/live_estate.py), [`lineage.json`](fixtures/datahub_recording/responses/lineage.json) |
| Downstream graph | Converts a finding into the exact partner, model, and analytics impact boundary | [`live_estate.py`](src/mosaic/live_estate.py), [`downstream.json`](fixtures/datahub_recording/responses/downstream.json) |
| Python SDK | Creates isolated synthetic assets and reads catalog entities through supported interfaces | [`live_estate.py`](src/mosaic/live_estate.py), [`entity.json`](fixtures/datahub_recording/responses/entity.json) |
| GraphQL API | Creates structured governance context and active incidents, then verifies them | [`datahub_graphql.py`](src/mosaic/datahub_graphql.py), [`writeback.json`](fixtures/datahub_recording/responses/writeback.json) |
| MCP Server | Gives an MCP-compatible agent schema, search, lineage, and tag tools | [`mcp_probe.py`](src/mosaic/mcp_probe.py), [`mcp.json`](fixtures/datahub_recording/responses/mcp.json) |
| DataHub Skill | Packages the reusable privacy workflow, safety policy, judgment, and failure handling | [`SKILL.md`](skills/datahub-privacy-threat-model/SKILL.md), [skill evaluations](skills/datahub-privacy-threat-model/evaluations) |
| Governed write-back | Publishes a field tag, structured property, threat-model Document, and incident only after approval, then re-reads every mutation | [`governed_writeback.py`](src/mosaic/governed_writeback.py) |

The same map is machine-inspectable in the running product at [`/api/technology`](https://mosaic-datahub-production.up.railway.app/api/technology). A hash-verified recording makes the named SDK, GraphQL, MCP, lineage, downstream, and write-back semantics reproducible without asking a judge to provision infrastructure.

### What Mosaic adds beyond DataHub

- **Graph-native privacy reasoning:** detects risk produced by relationships that neither a field classifier nor an out-of-box metadata view can establish alone.
- **Aggregate-only proof:** a fail-closed SQL policy measures anonymity while keeping person-level rows at zero.
- **Merge-ready remediation codegen:** converts the selected mitigation into dbt code, an aggregate privacy test, policy-as-code, provenance, and PR documentation.
- **Tamper-evident institutional memory:** digest-backed evidence and re-read write-back make the decision inheritable by the next human or agent.

The no-lineage baseline finds zero cross-source convergences. Mosaic finds the hidden convergence, validates it, and traces every downstream consumer.

### Supporting technology

- **DuckDB** provides isolated, in-memory aggregate validation.
- **dbt artifacts** provide merge-ready models, schema contracts, and singular privacy tests.
- **FastAPI** exposes typed read-only product and operator APIs.
- **Playwright** verifies the judge journey, responsive states, and accessibility in light and dark modes.

Mosaic also contributed back to its core platform: [`datahub-project/datahub#18705`](https://github.com/datahub-project/datahub/pull/18705) was merged upstream.

## Safety boundary

Mosaic is designed to measure exposure without identifying anyone:

- synthetic presets contain no real people;
- external rows are processed in memory and never committed;
- queries return counts only and reject row projections, joins, filters, mutations, and extra statements;
- raw rows returned is always recorded and must be zero;
- the hosted deployment is read-only;
- local browser write-back requires an environment opt-in, CSRF token, and exact phrase;
- every mutation is re-read and must verify.

Thresholds are demo policy, not a legal conclusion. Read [ETHICS.md](ETHICS.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

## Reusable interfaces

- REST: `/api/scenarios`, `/api/remediation-bundles/{slug}`, `/api/remediation-bundles/{slug}/download`, `/api/scan`, `/api/runs/{id}`, `/api/proofs`, `/api/adoption`, `/api/technology`
- CLI: `assess`, `generate-remediation`, `scan`, `benchmark`, `replay-fixture`, `serve`, `live-demo`, `verify-mcp`
- Agent skill: [`$datahub-privacy-threat-model`](skills/datahub-privacy-threat-model/SKILL.md)
- Operator console: `/settings` with non-mutating health probe and guarded local approval

## Development and verification

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=mosaic --cov-report=term-missing --cov-fail-under=99
uv build
uv run python scripts/check_cli_contracts.py
uv run python scripts/check_json_deliverables.py
uv run python scripts/check_utf8.py
```

CI repeats these gates on Ubuntu and Windows with Python 3.11 and 3.12, then runs browser accessibility checks across light and dark themes.

## Live DataHub proof

Use a disposable local DataHub Core instance, never a production catalog:

```powershell
uv sync --locked --extra dev --extra datahub
uv run mosaic live-demo --server http://localhost:8080
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

The first command stays dry-run. The approved command creates uniquely named synthetic targets and re-reads the field tag, structured property, threat-model Document, and incident.

## Project status and limitations

Mosaic has a merged upstream DataHub contribution: [datahub-project/datahub#18705](https://github.com/datahub-project/datahub/pull/18705). The primary product works offline and the recorded integration is reproducible. Production deployment still requires organization-approved thresholds, authenticated warehouse adapters, asset allowlists, access controls, and a fresh live compatibility run.

Apache-2.0 licensed. See [docs/ADOPTION_GUIDE.md](docs/ADOPTION_GUIDE.md) for the path from zero-setup exploration to production controls, [SUBMISSION.md](SUBMISSION.md) for the concise judge narrative, and [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the under-three-minute demo.