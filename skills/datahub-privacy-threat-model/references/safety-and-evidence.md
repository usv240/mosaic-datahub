# Safety and evidence policy

## Proof tiers

1. Configuration-driven synthetic scenarios prove deterministic product behavior.
2. The hash-verified DataHub recording proves expected SDK, GraphQL, MCP, lineage, downstream, and write-back semantics for the versioned fixture.
3. The aggregate-only UCI Adult proof demonstrates the composition mechanism on an external dataset without committing person-level rows.
4. A live local DataHub run proves compatibility with the operator's environment.

Never promote a lower tier into a stronger claim. A fixture is not a live connection; a benchmark is not field accuracy; an external historical dataset is not evidence of present-day population prevalence.

## Query invariants

- Allow only `COUNT(*)` plus approved grouping columns.
- Allow only the approved asset and explicitly identified quasi-identifiers.
- Reject `SELECT *`, row projections, direct identifiers, samples, exports, and row-level logging.
- Persist aggregate metrics and query text, never class values or source rows.
- Record `raw_rows_returned: 0` in evidence.

## Mutation invariants

- Default to dry run.
- Treat approval as exact boolean authorization for a named operation.
- Keep the hosted deployment read-only regardless of local settings.
- Publish only synthetic evidence targets from the browser workflow.
- Re-read every written evidence type; a mutation without successful re-read is `verification_failed`.
- Preserve target URNs, timestamps, configuration hashes, and evidence digests for review.

## Handling failures

- Integrity mismatch: quarantine the bundle and regenerate it.
- Query policy failure: issue no data query.
- DataHub connection failure: retain the dry-run proposal and report the unavailable dependency.
- Partial write or failed re-read: report each failed check and do not retry mutations without operator review.
