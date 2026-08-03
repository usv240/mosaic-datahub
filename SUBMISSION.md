# Mosaic submission

## One-line summary

Mosaic is a DataHub-grounded privacy remediation code-generation agent. It finds ordinary attributes that converge into dangerously small anonymity sets, validates the risk with aggregate-only queries, and generates a review-ready dbt remediation PR without exposing person-level rows.

## Links

- Live read-only demo: https://mosaic-datahub-production.up.railway.app
- Public repository: https://github.com/usv240/mosaic-datahub
- Narrated demo: [`docs/demo/mosaic-submission-demo.mp4`](docs/demo/mosaic-submission-demo.mp4) (2:49, upload-ready; public YouTube/Vimeo URL remains the sole external publication step)
- Merged DataHub contribution: https://github.com/datahub-project/datahub/pull/18705
- Official external dataset: https://archive.ics.uci.edu/dataset/2/adult

## Challenge fit

**Metadata-Aware Code Generation & Development.** Mosaic reads real schema, fine-grained lineage, downstream impact, and governance context from DataHub before generating a dbt model, schema contract, aggregate-only test, policy-as-code, provenance manifest, and PR summary that a data team can inspect and merge.

## The problem

A PII scanner asks whether one column is sensitive. Mosaic asks whether several non-PII columns become identifying after pipelines bring them together. ZIP code, birth date, and demographic category can look ordinary in separate systems while their combination creates singleton groups in an export. That is a graph property, not a column property.

## Judge path

The hosted product teaches the problem in plain language, then lets a judge choose among four working backend scenarios: a critical research export, a successfully mitigated shadow export, a safe operational control, and a second-domain audience export. The manual case explorer never auto-runs, advances an evidence step, moves to another case, scrolls, or opens comparison on a timer: judges start a case, reveal each of six steps by click, inspect, move next, and compare on demand. Every preset loads configuration-backed results from the API rather than swapping client-only labels.

The main critical fixture has 120 synthetic records, minimum k=1, 100% below k=5, three downstream assets, and zero raw rows returned. The selected mitigation reaches minimum k=20 in shadow mode. Mosaic then generates six deterministic, hash-verified PR artifacts; judges can review them in the product, download a ZIP, run the CLI, or inspect two committed examples.

## How DataHub powers the agent

DataHub is Mosaic's reasoning substrate and action layer. The agent uses seven concrete platform surfaces:

1. Fine-grained lineage reconstructs ordinary columns that originate separately and converge in one asset.
2. The downstream graph turns the validated finding into an estate-wide impact boundary.
3. The Python SDK creates isolated synthetic assets and reads supported catalog entities.
4. GraphQL creates and verifies structured governance context and active incidents.
5. The MCP Server exposes search, entity, lineage, and tag tools to an MCP-compatible agent.
6. A packaged DataHub Skill makes the workflow, safety policy, judgment, and failure handling reusable.
7. Governed write-back publishes a tag, structured property, threat-model Document, and incident only after human approval, then re-reads every mutation.

Mosaic adds graph-native privacy reasoning, a fail-closed aggregate-only proof layer, a reversible mitigation lab, merge-ready remediation code generation, and tamper-evident evidence retention beyond DataHub's out-of-box metadata experience. The complete implementation map is inspectable at `/api/technology`, and the team contributed back through merged upstream PR [datahub-project/datahub#18705](https://github.com/datahub-project/datahub/pull/18705).
Generated output is not trusted merely because it was generated. Mosaic enforces typed dbt contracts, compiles generated SQL, rejects unstructured or injection-shaped DataHub context, records per-file digests, and requires a named human review boundary. These controls are mapped to official DataHub, dbt, NIST, and OWASP sources in [`docs/RESEARCH_FOUNDATIONS.md`](docs/RESEARCH_FOUNDATIONS.md).

## Evidence, not assertion

Mosaic separates five proof tiers:

1. Four configuration-driven synthetic scenarios prove deterministic product behavior.
2. A hash-verified recording proves versioned DataHub SDK, GraphQL, MCP, lineage, downstream, and write-back semantics.
3. A 48-case seeded benchmark proves exact metric agreement and policy-boundary regression behavior, with 100% precision/recall only for its deliberately bounded generated families.
4. Two committed remediation bundles prove deterministic generation of six review-ready artifacts with per-file SHA-256 receipts and safe refusal for a negative control.
5. An aggregate-only proof processes 32,561 official UCI Adult records in memory. Age band alone has minimum k=43; six ordinary attributes composed have minimum k=1 and 23.786% below k=5. No source row or equivalence-class value is committed.

These are mechanism and integration claims, not legal conclusions or estimates of production prevalence. A live local DataHub run is the strongest environment-specific proof: the discovered asset URN, schema, lineage paths, and downstream boundary directly drive a six-file bundle whose generated SQL is compiled before it is returned.

## Safety and governance

Mosaic permits only allow-listed `GROUP BY COUNT(*)` validation, returns zero person-level rows, and refuses catalog mutation by default. Browser write-back is disabled unless a local operator opts in, obtains a same-origin CSRF token, and types an exact confirmation phrase. The hosted deployment remains read-only regardless of that setting. Every retained evidence bundle and generated code artifact carries a SHA-256 digest. Generated code is proposal-only: the hosted product cannot commit, merge, execute, or mutate DataHub.

## Engineering quality

The repository includes a locked environment, distributable wheel and source package, multi-OS and multi-Python CI, 99% coverage enforcement, strict JSON and encoding checks, CLI contract gates, benchmark and fixture replay gates, and browser accessibility checks across light and dark themes. The packaged `$datahub-privacy-threat-model` skill makes the workflow reusable by another agent.

## Honest limitations

The primary scenarios are synthetic by design. The UCI Adult dataset is census-derived historical data and is used only as a reproducible composition-mechanism check. Thresholds are demo policy, not law. The recorded DataHub fixture proves normalized semantics for named versions, not current server availability. Production use requires organization-approved policy, warehouse adapters, access controls, authentication, and a live DataHub validation run.