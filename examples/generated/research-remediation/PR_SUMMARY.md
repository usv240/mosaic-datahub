# Privacy remediation: Research export investigation

## Why this change exists

DataHub fine-grained lineage revealed 3 quasi-identifier families
converging across 2 source systems in `research_export_clean`. Mosaic's
aggregate-only validation measured minimum k=1 with
zero person-level rows returned.

## Proposed code change

Suppress precise birth_date while retaining ZIP5 and demographic category. The shadow result reaches minimum k=20
with 76% measured utility retained in the
synthetic scenario. These thresholds are review policy, not a legal conclusion.

## DataHub context used

- Source asset: `urn:li:dataset:(urn:li:dataPlatform:mosaic,research_export_clean,PROD)`
- Scenario digest: `5626a6b7e08141a5857dbe771a3dabaf74672778211ea3e2cf96e2a5b8dc9bab`
- Context trust: structured metadata allowlist; free-form instructions are rejected
- Fine-grained lineage:
- `support_contacts.zip5` -> `research_export_clean.zip5`
- `support_contacts.full_birth_date` -> `research_export_clean.birth_date`
- `member_demographics_coarse.gender_category` -> `research_export_clean.gender_category`
- Downstream review boundary:
- `research_partner_delivery`
- `cohort_explorer_export`
- `readmission_model_training`

## Review checklist

- [ ] Data owner confirms the generated column contract.
- [ ] Privacy reviewer approves the organization-specific threshold.
- [ ] CI runs the aggregate-only minimum-k dbt test.
- [ ] Reviewer inspects downstream compatibility before merge.
- [ ] Approved result is written back to DataHub and re-read.

Generated artifacts are proposals. Mosaic does not commit, merge, or execute them.
