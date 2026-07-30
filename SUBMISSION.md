# Mosaic submission

## One-line summary

Mosaic is a DataHub-grounded privacy threat-modeling agent that finds when ordinary attributes converge through lineage into dangerously small anonymity sets, validates the risk with aggregate-only queries, traces downstream exposure, and proposes approval-gated remediation.

## Links

- Live read-only demo: https://mosaic-datahub-production.up.railway.app
- Public repository: https://github.com/usv240/mosaic-datahub
- Merged DataHub contribution: https://github.com/datahub-project/datahub/pull/18705
- Official external dataset: https://archive.ics.uci.edu/dataset/2/adult

## Challenge fit

Open / Wildcard, with an agent that does real work across discovery, validation, prioritization, mitigation, evidence retention, and governed DataHub write-back.

## The problem

A PII scanner asks whether one column is sensitive. Mosaic asks whether several non-PII columns become identifying after pipelines bring them together. ZIP code, birth date, and demographic category can look ordinary in separate systems while their combination creates singleton groups in an export. That is a graph property, not a column property.

## Judge path

The hosted product teaches the problem in plain language, then offers four working backend scenarios: a critical research export, a successfully mitigated shadow export, a safe operational control, and a second-domain audience export. Every preset loads configuration-backed results from the API rather than swapping client-only labels.

The main critical fixture has 120 synthetic records, minimum k=1, 100% below k=5, three downstream assets, and zero raw rows returned. The mitigation generalizes or suppresses an attribute in shadow mode and reaches minimum k=20 without touching source data.

## Why DataHub is essential

Fine-grained DataHub lineage reveals that quasi-identifier families originate in separate source systems and converge in one asset. A no-lineage baseline finds zero cross-source convergences; Mosaic finds the convergence and its downstream blast radius. DataHub also becomes durable governance memory through an approved field tag, structured risk property, linked threat-model Document, and active incident, all re-read after publication.

## Evidence, not assertion

Mosaic separates four proof tiers:

1. Four configuration-driven synthetic scenarios prove deterministic product behavior.
2. A hash-verified recording proves versioned DataHub SDK, GraphQL, MCP, lineage, downstream, and write-back semantics.
3. A 48-case seeded benchmark proves exact metric agreement and policy-boundary regression behavior, with 100% precision/recall only for its deliberately bounded generated families.
4. An aggregate-only proof processes 32,561 official UCI Adult records in memory. Age band alone has minimum k=43; six ordinary attributes composed have minimum k=1 and 23.786% below k=5. No source row or equivalence-class value is committed.

These are mechanism and integration claims, not legal conclusions or estimates of production prevalence. A live local DataHub run is the strongest environment-specific proof.

## Safety and governance

Mosaic permits only allow-listed `GROUP BY COUNT(*)` validation, returns zero person-level rows, and refuses catalog mutation by default. Browser write-back is disabled unless a local operator opts in, obtains a same-origin CSRF token, and types an exact confirmation phrase. The hosted deployment remains read-only regardless of that setting. Every retained bundle carries a SHA-256 digest and a human-readable print/PDF view.

## Engineering quality

The repository includes a locked environment, distributable wheel and source package, multi-OS and multi-Python CI, 99% coverage enforcement, strict JSON and encoding checks, CLI contract gates, benchmark and fixture replay gates, and browser accessibility checks across light and dark themes. The packaged `$datahub-privacy-threat-model` skill makes the workflow reusable by another agent.

## Honest limitations

The primary scenarios are synthetic by design. The UCI Adult dataset is census-derived historical data and is used only as a reproducible composition-mechanism check. Thresholds are demo policy, not law. The recorded DataHub fixture proves normalized semantics for named versions, not current server availability. Production use requires organization-approved policy, warehouse adapters, access controls, authentication, and a live DataHub validation run.