# Privacy remediation: Partner audience export

## Why this change exists

DataHub fine-grained lineage revealed 3 quasi-identifier families
converging across 3 source systems in `partner_audience_export`. Mosaic's
aggregate-only validation measured minimum k=1 with
zero person-level rows returned.

## Proposed code change

Generalize neighborhood to region and suppress household_size. The shadow result reaches minimum k=8
with 71% measured utility retained in the
synthetic scenario. These thresholds are review policy, not a legal conclusion.

## DataHub context used

- Source asset: `urn:li:dataset:(urn:li:dataPlatform:mosaic,partner_audience_export,PROD)`
- Scenario digest: `77e00c31c263d925d571fa5ca1db949e0c4bb2b4d41c73e59f8820242f576576`
- Context trust: structured metadata allowlist; free-form instructions are rejected
- Fine-grained lineage:
- `customer_addresses.neighborhood` -> `partner_audience_export.neighborhood`
- `customer_profiles.age_band` -> `partner_audience_export.age_band`
- `billing_households.household_size` -> `partner_audience_export.household_size`
- Downstream review boundary:
- `ad_partner_delivery`
- `campaign_activation`

## Review checklist

- [ ] Data owner confirms the generated column contract.
- [ ] Privacy reviewer approves the organization-specific threshold.
- [ ] CI runs the aggregate-only minimum-k dbt test.
- [ ] Reviewer inspects downstream compatibility before merge.
- [ ] Approved result is written back to DataHub and re-read.

Generated artifacts are proposals. Mosaic does not commit, merge, or execute them.
