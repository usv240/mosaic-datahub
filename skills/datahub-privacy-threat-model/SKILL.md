---
name: datahub-privacy-threat-model
description: Assess compositional re-identification risk by combining DataHub schema, tags, lineage, and downstream impact with aggregate-only k-anonymity validation. Use when asked to find privacy risk across datasets, inspect quasi-identifier convergence, compare a metadata-only baseline with lineage-aware discovery, produce governed DataHub evidence, scan configured Mosaic scenarios, or explain and mitigate small anonymity sets without exposing person-level rows.
---

# DataHub Privacy Threat Model

Use Mosaic to find graph-shaped privacy risk: ordinary columns that become identifying only after lineage brings them together. Keep discovery metadata-first, validate with aggregate counts only, and separate proposals from approved catalog mutations.

## Workflow

1. Establish scope and safety.
   - Identify the DataHub server, assets or domain, and review owner.
   - Default to read-only and dry-run behavior.
   - Never request, print, retain, or commit identity-bearing rows.
2. Discover candidates from DataHub metadata.
   - Inspect schemas, semantic tags, upstream lineage, and downstream consumers.
   - Require multiple quasi-identifier families and a credible person-join path.
   - Do not classify a column as risky from cardinality alone.
3. Validate only credible candidates.
   - Generate an allow-listed `COUNT(*) ... GROUP BY` query.
   - Reject projections, wildcards, samples, row identifiers, and unapproved assets or columns.
   - Record minimum k, percentages below k=2/5/10, class-size distribution, and raw rows returned (`0`).
4. Explain the graph advantage.
   - Compare lineage-aware candidate count with the same screening logic without lineage.
   - Name source systems, convergence paths, and downstream blast radius.
5. Propose mitigation.
   - Compare generalization, suppression, access controls, and purpose limitation.
   - Recommend a concrete owner and next review point.
6. Publish only after explicit approval.
   - Prefer a retained evidence bundle first.
   - Require an explicit approval flag or the browser's exact confirmation phrase.
   - Re-read every tag, structured property, document, and incident after mutation.
7. Report evidence and limitations.
   - Link the run detail or canonical JSON and include its SHA-256 digest.
   - Distinguish synthetic regression, recorded DataHub replay, and external-data evidence.
   - Never describe fixture performance as production accuracy.

## Commands

Run from the Mosaic repository:

```bash
uv run mosaic scan
uv run mosaic assess --scenario research
uv run mosaic replay-fixture
uv run mosaic benchmark
uv run mosaic serve --host 127.0.0.1 --port 8000
```

For a live local DataHub proof, first read [references/safety-and-evidence.md](references/safety-and-evidence.md), then use the CLI without approval to inspect the dry run. Add `--approve-writeback` only after the user explicitly authorizes catalog mutation.

Use `scripts/verify_evidence.py PATH` to validate the digest of a retained Mosaic run before relying on it.

## Verdict rules

- `screening_only`: metadata did not justify a data query; do not imply measured risk.
- `validated_low`: aggregate validation found no small classes under the configured policy.
- `validated_elevated`: exact metrics show meaningful small-class exposure below the critical rule.
- `validated_critical`: minimum k is below 2 and at least 20% of records are below k=5.

Do not weaken or silently alter these boundaries. If an organization has a different approved policy, make it explicit and versioned.

## Output contract

Return a concise decision followed by evidence:

- scenario and asset URN;
- verdict and exact metrics, or why no query was issued;
- lineage paths, source systems, and downstream count;
- query safety result and raw rows returned;
- mitigation, owner, and approval state;
- run ID, configuration hash, evidence hash, and proof tier;
- limitations and the next human decision.

If any integrity check, re-read, or safety gate fails, say so prominently and do not report the workflow as complete.