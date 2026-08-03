# Mosaic

> No column here is PII. Together, they identify you.

**[Try the read-only live demo](https://mosaic-datahub-production.up.railway.app)**

**Challenge: Metadata-Aware Code Generation & Development**

Mosaic is a DataHub-grounded privacy remediation code-generation agent. It discovers ordinary attributes that become identifying only after pipelines bring them together, validates the combination with aggregate-only anonymity metrics, traces the downstream blast radius, compares mitigations, generates a merge-ready remediation bundle, and prepares governed catalog evidence for human approval.

A PII scanner classifies columns. Mosaic reasons over the graph.

**Mosaic is not a new k-anonymity algorithm; its contribution is deciding where to measure.** Established anonymization tools begin with a supplied dataset and attribute roles. Mosaic derives candidate quasi-identifiers from DataHub's column-level lineage across assets and systems, then measures the combination and generates a governed remediation change.

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
### Best first demo: inspect all four decisions at your pace

On the landing page, choose **Open case explorer**. Select a case and press **Start selected case**. Step 1 opens immediately; after reading it, press **Continue to step N of 6** five times. Waiting never advances the evidence. Choose **Next case** and **Compare results** only when you are ready:

| Case | Expected decision | What it proves |
|---|---|---|
| Research export | Critical, `k=1`, three downstream assets | DataHub column lineage reveals cross-source risk that per-table checks miss |
| Mitigated export | Safe, `k=20`, 76% utility retained | Mosaic verifies a reversible fix instead of treating every dataset as permanently unsafe |
| Negative control | Clear; no warehouse query and no generated code | Mosaic refuses to invent a finding or access data without sufficient metadata evidence |
| Audience delivery | Critical, `k=1`, two downstream assets | The mechanism generalizes to a second business domain rather than one memorized fixture |

Every case returns zero person-level rows. No case, evidence step, next-case transition, comparison, or page scroll advances on a timer. After the scorecard, use **Run locally** for the reproducible CLI, **Plan adoption** for connector and control requirements, or **Inspect evidence** for retained receipts. For a technical review, inspect Finding, Validation query, Attack lab, Mitigation lab, Remediation PR, and DataHub proposal before moving next.

Or start the safe, read-only container path:

```powershell
docker compose up --build
```

The core CLI is completely offline:

```powershell
uv run mosaic assess --scenario research
uv run mosaic assess --agent --scenario research --agent-model mistral:latest
uv run mosaic scan
uv run mosaic check --fail-on critical
uv run mosaic redteam
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

To inspect an existing DataHub asset that Mosaic did not seed, run:

```powershell
uv run mosaic discover --server http://localhost:8080 --urn "<dataset-urn>" --max-hops 3 --output evidence/external/datahub-live.json
```

The reader traverses schema plus column lineage, ranks QI evidence as glossary term > tag > type-and-name > name, and emits a convergence only when at least two families arrive from at least two upstream datasets. Empty lineage and single-source assets return no convergence rather than an invented finding.

For the opt-in agent path, a local Ollama-compatible model may select an allowlisted asset, nominate schema columns, explain its reasoning, and draft review text. It cannot construct or execute SQL, calculate the verdict, generate a policy, or mutate DataHub. Mosaic compiles the aggregate query deterministically and can veto the proposal. The default CLI remains fully deterministic and offline.

`uv run mosaic redteam` replays an indirect prompt injection placed in a DataHub dataset description. The hostile metadata asks for person-level identifiers; the query policy refuses it, records why, returns zero rows, and continues with its own aggregate-only query. The command exits non-zero if that refusal ever disappears.

The organization owns `.mosaic/privacy-policy.yml`. Changing its minimum-k threshold changes the backend verdict, generated dbt test, policy snapshot, and provenance digest. The included GitHub Action runs `mosaic check --fail-on critical` as a pre-merge gate. Snowflake is supported through an optional DB-API adapter (`uv sync --extra snowflake`). Run `uv run --extra snowflake mosaic verify-snowflake` to validate a scoped, query-tagged identity; the public receipt hashes session context and never stores credential values.

## What the agent does

1. Screens DataHub schemas, tags, fine-grained lineage, and downstream dependencies.
2. Derives QI families from ranked DataHub glossary, tag, schema-type, and name evidence; then requires multi-source convergence.
3. Builds and validates one aggregate-only `COUNT(*) ... GROUP BY` shape.
4. Measures minimum k and record percentages below k=2, k=5, and k=10.
5. Tests graph-only convergence, including cross-asset join risk no single-table scanner can express.
6. Ranks estate findings by severity, anonymity, and downstream reach.
7. Compares generalization, suppression, access control, and purpose limitation.
8. Runs an adversarial false-positive self-check, then generates a dbt model, contract, aggregate-only test, policy snapshot, manifest, and PR summary.
9. Records digest-backed evidence and prepares DataHub governance context.
10. Publishes only after explicit approval, then re-reads every mutation.

## Remediation PR Studio

Mosaic turns a validated graph finding into code a data team can review and merge. Generation is deterministic, digest-backed, and grounded in the selected scenario's DataHub URN, fine-grained lineage, schema, and downstream impact.

| Generated artifact | Purpose |
|---|---|
| `models/*_privacy_safe.sql` | dbt model implementing the selected suppression or generalization |
| `models/*_privacy_safe.yml` | Enforced typed column contract, DataHub URN, scenario digest, and before/after metrics |
| `tests/assert_*_minimum_k.sql` | Singular dbt test that returns only an aggregate failure metric |
| `.mosaic/privacy-policy.yml` | Review thresholds, required roles, and post-merge write-back plan |
| `mosaic-manifest.json` | DataHub context and SHA-256 digest for every generated artifact |
| `PR_SUMMARY.md` | Reviewer-ready rationale, lineage, blast radius, and approval checklist |

Inspect the committed [research](examples/generated/research-remediation) and [audience](examples/generated/audience-remediation) outputs, call `/api/remediation-bundles/{scenario}`, or download the reproducible ZIP from `/api/remediation-bundles/{scenario}/download`. A safe negative control produces no bundle; Mosaic refuses to manufacture unnecessary code.

### Research-backed controls

The generator follows the official [DataHub metadata-aware code-generation architecture](https://datahub.com/blog/build-with-datahub-agent-hackathon/): structured schema, lineage, and governance context must arrive before code, examples are committed for review, and output is validated before commit. Generated YAML uses [dbt enforced model contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts), while the minimum-k check follows dbt's [singular data-test contract](https://docs.getdbt.com/docs/build/data-tests): a test returns a failure row only when its assertion fails.

The privacy claim remains deliberately narrower than "anonymous." [NISTIR 8053](https://www.nist.gov/publications/de-identification-personal-information) explains both the risk-reduction value and the limits of de-identification. [OWASP's Secure Coding with AI guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) motivates Mosaic's structured context allowlist, injection rejection, validation, audit receipts, and mandatory human owner. See the complete [claim-to-control research map](docs/RESEARCH_FOUNDATIONS.md).

### Where Mosaic differs from anonymization tools

| System | Starting scope | Quasi-identifier input | Mosaic's distinct layer |
|---|---|---|---|
| [ARX](https://arx.deidentifier.org/anonymization-tool/configuration/) | One imported table | Users specify attribute metadata; ARX also provides detection and risk-analysis aids | DataHub lineage nominates cross-system combinations before a table is handed to an anonymizer |
| [sdcMicro](https://sdctools.github.io/sdcMicro/articles/ai_assisted_anonymization.html) | One in-memory microdata frame | Declared `keyVars`, with a newer optional AI-assisted classifier | Evidence is ranked from glossary, tags, schema, and column lineage across the estate |
| [Amnesia](https://amnesia.openaire.eu/using-amnesia/how-to-use.html) | A loaded tabular or set-valued dataset | A user associates each quasi-identifier with a hierarchy | Mosaic traces downstream blast radius and emits a reviewable dbt remediation bundle |
| **Mosaic** | DataHub's multi-platform metadata graph | Deterministic evidence plus an optional proposal-only model | Discovers graph composition, validates aggregate counts, and produces governed code without replacing those anonymizers |

This is a scope and workflow contribution, not a claim that Mosaic invented k-anonymity or supersedes mature statistical-disclosure-control software.

## Evidence ladder

| Proof | Result | Honest scope |
|---|---:|---|
| Configured scenarios | 4 working backend cases across two domains | Deterministic product behavior |
| Generated remediation | 2 committed bundles; 6 artifacts each; hashes reproducible | Review-ready examples, not automatically merged code |
| Regression benchmark | 48 cases plus a 10,000-column catalog scan; exact agreement 100% | Deliberately bounded policy and scale regression, not field accuracy |
| DataHub recording replay | Hashes and semantic checks pass | Versioned normalized integration semantics, not a live server |
| Official DataHub showcase catalog | Positive: 55 fields, 17 classified, 3 families, 10 true upstream datasets; negative: single-source asset refused | Two live quickstart receipts against a DataHub-authored pack; metadata screening, not a warehouse verdict or prevalence claim |
| Local model boundary | 1 Mistral proposal accepted for human review; 1 under-supported proposal vetoed; 0 generated statements executed | Recorded local Ollama runs; deterministic policy owns SQL and verdict |
| Metadata prompt-injection replay | Hostile DataHub description refused; safe run continued; 0 raw rows | Deterministic transcript and acceptance gate; not a claim that every possible injection is solved |
| UCI Adult external proof | 32,561 rows processed in memory; k=43 to k=1 after composition; 23.786% below k=5 | Historical external mechanism check, not current prevalence |
| Live local DataHub workflow | Schema, lineage, downstream, generated six-file remediation, SQL compile, write-back, and re-read | Environment-specific proof when the operator runs it |

See [evaluations/benchmark.json](evaluations/benchmark.json), [fixtures/datahub_recording/manifest.json](fixtures/datahub_recording/manifest.json), [the prompt-injection transcript](fixtures/agent_transcripts/prompt-injection.json), [the official-catalog positive proof](evidence/external/DATAHUB_SHOWCASE_PROOF.md), [its machine-readable receipt](evidence/external/datahub-showcase-positive-live.json), [the fail-closed negative control](evidence/external/datahub-showcase-ecommerce-live.json), [the accepted and vetoed local-model receipts](evidence/external/ollama-agent-accepted-live.json), [the Snowflake readiness receipt](evidence/external/snowflake-live.json), and [the UCI Adult proof](evidence/external/uci-adult-proof.json).

## Product tour

**Start here: four decisions in a manual case explorer**

[![Mosaic manually verified four-case scorecard](docs/screenshots/12-four-case-scorecard.png)](docs/screenshots/12-four-case-scorecard.png)
| First-visit education | Guided investigation |
|---|---|
| [![Mosaic landing page in dark mode](docs/screenshots/01-landing-dark.png)](docs/screenshots/01-landing-dark.png) | [![Completed privacy investigation](docs/screenshots/03-completed-investigation.png)](docs/screenshots/03-completed-investigation.png) |
| **Evidence catalog** | **Responsive light mode** |
| [![Reproducible proof catalog](docs/screenshots/04-evidence-catalog.png)](docs/screenshots/04-evidence-catalog.png) | [![Mosaic landing page in light mode](docs/screenshots/06-landing-light.png)](docs/screenshots/06-landing-light.png) |
| **Remediation PR Studio** | **DataHub architecture** |
| [![Generated remediation code review](docs/screenshots/09-remediation-pr.png)](docs/screenshots/09-remediation-pr.png) | [![DataHub technology architecture](docs/screenshots/08-datahub-architecture.png)](docs/screenshots/08-datahub-architecture.png) |
| **Research-backed controls** | **Audience scenario** |
| [![Research and standards receipts](docs/screenshots/10-research-standards.png)](docs/screenshots/10-research-standards.png) | [![Audience preset](docs/screenshots/02-audience-preset.png)](docs/screenshots/02-audience-preset.png) |

The repository also includes the complete [screenshot gallery](docs/screenshots/README.md), [interactive source footage](docs/demo/08-product-walkthrough.webm), and the final [2:50 narrated submission video](docs/demo/mosaic-submission-demo.mp4). The MP4 is upload-ready and verified under three minutes; a YouTube/Vimeo URL remains an external publication receipt and is not claimed until uploaded.

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

The new [Compositional Privacy Metadata RFC](docs/COMPOSITIONAL_PRIVACY_RFC.md) packages Mosaic's QI-family, join-key, evidence, validation, and human-review vocabulary for reuse by DataHub adopters and other agents.

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

- REST: `/api/scenarios`, `/api/remediation-bundles/{slug}`, `/api/remediation-bundles/{slug}/download`, `/api/scan`, `/api/agent-receipts`, `/api/redteam`, `/api/runs/{id}`, `/api/proofs`, `/api/adoption`, `/api/technology`
- CLI: deterministic `assess`; opt-in `assess --agent`; `discover`, `generate-remediation`, `scan`, `check`, `redteam`, `benchmark`, `replay-fixture`, `serve`, `live-demo`, `verify-mcp`, `verify-snowflake`
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

Mosaic has a merged upstream DataHub contribution: [datahub-project/datahub#18705](https://github.com/datahub-project/datahub/pull/18705). The primary product works offline and the recorded integration is reproducible. Mosaic now accepts organization-owned thresholds, includes a Snowflake adapter boundary, and ships a pre-merge gate. Production deployment still requires real warehouse credentials, asset allowlists, SSO/RBAC, policy owners, and a fresh compatibility run against the target DataHub and warehouse.

Apache-2.0 licensed. See [docs/ADOPTION_GUIDE.md](docs/ADOPTION_GUIDE.md) for the path from zero-setup exploration to production controls, [SUBMISSION.md](SUBMISSION.md) for the concise judge narrative, and [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the under-three-minute demo.

Before publication, run `uv run python scripts/final_submission_audit.py --online`. The audit fails closed unless the public video receipt exists and both GitHub and Railway serve the current commit. For local review before authenticated video upload, add `--allow-pending-video`.