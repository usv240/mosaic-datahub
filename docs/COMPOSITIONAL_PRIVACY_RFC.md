# RFC: Compositional Privacy Metadata for DataHub

Status: reference proposal implemented by Mosaic
Audience: data platform, privacy engineering, governance, and agent-tooling teams

## Summary

Field-level PII labels answer whether a field is sensitive by itself. They do not represent risk created when ordinary fields from independent assets become joinable or converge downstream. This RFC proposes a small DataHub-native vocabulary and a fail-closed decision contract for that missing layer.

The proposal does not label a person, store raw rows, or declare data anonymous. It records inspectable metadata evidence, an aggregate validation boundary, and a human-owned remediation decision.

## Metadata vocabulary

| Key | Scope | Type | Meaning |
|---|---|---|---|
| `privacy.qi_family` | schema field | enum | Semantic family such as `location`, `date_of_birth`, `demographic`, `financial`, `device`, or `temporal` |
| `privacy.qi_evidence` | schema field | string | Ranked source: glossary term, tag, schema type plus name, or name-only heuristic |
| `privacy.entity_join_key` | schema field | boolean | Field can join records about the same governed entity; this is not permission to query it |
| `privacy.convergence_sources` | dataset | URN list | Independent upstream datasets contributing QI families |
| `privacy.validation_mode` | dataset | enum | `metadata_screening`, `aggregate_validated`, or `insufficient_evidence` |
| `privacy.minimum_k` | dataset/finding | integer | Smallest measured equivalence class from an approved aggregate query |
| `privacy.percent_below_k5` | dataset/finding | number | Percentage of records represented by classes smaller than five |
| `privacy.raw_rows_returned` | finding | integer | Must be zero for a Mosaic-compatible assessment |
| `privacy.evidence_sha256` | finding/document | string | Digest of the normalized evidence bundle |
| `privacy.review_status` | finding/document | enum | `screening_candidate`, `validated`, `mitigation_proposed`, `approved`, `rejected` |

Use DataHub glossary terms when an organization already owns a semantic vocabulary. Use tags for established classifications. Use structured properties for typed policy state and evidence references. Use Documents for the threat-model narrative and Incidents for active remediation workflow.

## Deterministic convergence rule

A metadata screening candidate exists only when all are true:

1. at least two distinct QI families are supported by visible evidence;
2. those families have column-lineage origins in at least two true dataset URNs;
3. self-edges and data-job nodes are excluded from the dataset count; and
4. for cross-asset screening, both assets share an explicit entity join key and each contributes context the other does not.

A screening candidate is not a critical verdict. An organization policy must authorize an aggregate-only `GROUP BY ... COUNT(*)` validation before Mosaic can calculate minimum k or percentages below a threshold.

## Agent authority boundary

An agent or language model may:

- choose among assets already returned by DataHub;
- nominate columns present in the catalog schema;
- explain its evidence; and
- draft a review narrative.

It may not:

- invent an asset, column, lineage edge, or glossary classification;
- construct or execute warehouse SQL;
- decide the verdict or policy threshold;
- publish a tag, property, document, or incident; or
- merge generated remediation code.

A deterministic verifier allowlists the context, compiles the aggregate query, calculates metrics, validates generated artifacts, and can veto the proposal. Human approval remains mandatory for code or catalog mutation.

## DataHub write-back mapping

| Decision artifact | DataHub primitive | Verification |
|---|---|---|
| Field classification | tag or glossary term | re-read exact field association |
| Typed assessment state | structured properties | re-read values and policy/evidence digest |
| Threat model and limitations | Document | re-read body and linked dataset |
| Active mitigation work | Incident | re-read state, priority, and linked asset |
| Impact boundary | upstream/downstream lineage | re-query after write-back; lineage itself is not mutated |

## Interoperability and adoption

The vocabulary is intentionally connector-agnostic. A Snowflake, BigQuery, dbt, Postgres, or lakehouse asset uses the same semantic families and decision states. Start in report-only mode, require glossary/tag evidence for higher-confidence automation, then add the pre-merge gate only after policy owners review false positives and thresholds.

The reusable agent workflow is packaged in [`skills/datahub-privacy-threat-model/SKILL.md`](../skills/datahub-privacy-threat-model/SKILL.md). The reference implementation lives in [`src/mosaic/catalog_reader.py`](../src/mosaic/catalog_reader.py), [`src/mosaic/compositional_join.py`](../src/mosaic/compositional_join.py), and [`src/mosaic/agent_proposer.py`](../src/mosaic/agent_proposer.py).

## Evidence and limits

- Positive foreign-catalog receipt: [`evidence/external/DATAHUB_SHOWCASE_PROOF.md`](../evidence/external/DATAHUB_SHOWCASE_PROOF.md)
- Fail-closed negative control: [`evidence/external/datahub-showcase-ecommerce-live.json`](../evidence/external/datahub-showcase-ecommerce-live.json)
- Accepted and vetoed model proposals: [`evidence/external/ollama-agent-accepted-live.json`](../evidence/external/ollama-agent-accepted-live.json) and [`evidence/external/ollama-agent-veto-live.json`](../evidence/external/ollama-agent-veto-live.json)
- Research and standards map: [`docs/RESEARCH_FOUNDATIONS.md`](RESEARCH_FOUNDATIONS.md)

Open questions for production adopters include entity-key governance, confidence calibration by domain, policy ownership across jurisdictions, retention of evidence bundles, and compatibility across DataHub server versions. None of those should be silently defaulted by an agent.