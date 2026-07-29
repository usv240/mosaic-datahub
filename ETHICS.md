# Mosaic safety boundary

Mosaic assesses anonymity-set risk; it does not identify people.

- Demo records are deterministic and fictional. No real patient, voter, customer, or
  public person-level auxiliary data is used.
- The engine keeps record values inside the aggregate calculator and reports only
  counts, distributions, and downstream asset names.
- The query policy is fail-closed: one known asset, approved quasi-identifier fields,
  `COUNT(*)`, and `GROUP BY`. It rejects joins and non-aggregate output.
- A recommendation is shadow-only until a privacy/security reviewer approves a catalog
  mutation. Mosaic never changes source data or access controls.
- A risk verdict is not a legal conclusion. Thresholds are visible project policy and
  must be tailored and reviewed for any real deployment.
