# Evaluation contract

The offline suite must keep these invariants true:

| Invariant | Why it matters |
|---|---|
| Hero convergence is critical | The central defect remains detectable. |
| Generalized control clears | Mosaic does not flag every high-cardinality asset. |
| No-lineage baseline finds less | DataHub graph context is materially useful. |
| Raw rows returned is zero | The agent measures risk without exposing records. |
| Query policy rejects joins/mutations | Aggregate execution stays bounded and safe. |
| Write-back requires approval | Catalog mutations remain reviewer-controlled. |

`pytest` enforces the offline contract. `scripts/run_live_e2e.py` separately proves
the local DataHub Core and DuckDB integration path using uniquely named synthetic
assets.
