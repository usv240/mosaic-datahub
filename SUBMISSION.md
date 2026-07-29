# Mosaic â€” submission draft

## One-line summary

Mosaic is a DataHub-grounded privacy threat-modeling agent that detects when harmless
columns converge through lineage into small anonymity sets, validates the risk with
aggregate-only queries, traces downstream exposure, and proposes an approval-gated
mitigation.

## Challenge

Open / Wildcard, with Agents That Do Real Work.

## What makes it different

Data classification answers, â€œis this column PII?â€ Mosaic answers the harder estate
question: â€œwhen these non-PII columns meet through our pipelines, does the resulting
asset create dangerously small anonymity sets?â€ Fine-grained DataHub lineage makes
that question discoverable across systems; a per-table scanner cannot answer it.

## Measured demo result

The frozen synthetic research-export fixture has 120 records and a convergence of ZIP5,
birth date, and gender. Exact aggregate validation finds 120 distinct combinations,
`minimum k=1`, and 100% of records below `k=5`. Suppressing birth date in shadow mode
produces `minimum k=20`. Mosaic returns zero raw rows throughout.

The graph-value control finds one lineage-only convergence; a no-lineage per-table
baseline finds zero. Safe controls for a generalized export, a tagged direct identifier,
a non-person operational ID, and an aggregate dashboard all avoid critical findings.

## DataHub use

Mosaic reads schemas and fine-grained column lineage from DataHub Core. Its live probe
seeds fresh synthetic assets and re-reads the resulting paths. After explicit approval,
it writes a `mosaic:validated-critical` field tag and a linked privacy threat-model
Document, then re-reads both mutations. The offline console makes each evidence item
visible without a local DataHub instance.

## Disclosure

All person-level fixture records are deterministic and fictional. Thresholds are demo
policy, not legal conclusions. The live write-back proof covers field tag, structured risk property, linked threat-model
Document, and active incident rereads. Official MCP search, column lineage, governed tag
mutation, and reread are verified. Fresh-edge Agent Context Kit behavior remains a
version-specific limitation and is not claimed as passed.
