# Proposed mitigation (review required)

Suppress `birth_date` from `research_export_clean` before research or partner delivery.

This is a shadow-only recommendation based on synthetic fixture aggregation. It leaves
the fixture with a minimum equivalence class size of 20 for `zip5 + gender_category`.
No source data, catalog metadata, or access policy is changed by this artifact.
