# Mosaic demo â€” 2:25 target

## 0:00â€“0:15 â€” The problem

Show the landing-page headline: â€œNo column here is PII. Together, they identify you.â€
Explain that a research export has no direct identifier, yet ordinary fields arrived
through different pipelines and now create tiny anonymity sets.

## 0:15â€“0:40 â€” Why DataHub

Select each attack-path node. Show the three lineage paths converging into the research
export. State that a per-table scanner sees separate harmless fields; DataHubâ€™s
fine-grained graph reveals where they meet.

## 0:40â€“1:05 â€” Exact, safe validation

Show the generated `GROUP BY COUNT(*)` query and the metric cards: `k=1`, 100% below
`k=5`, zero raw rows. Say clearly: Mosaic measures groups; it never identifies anyone.

## 1:05â€“1:30 â€” Blast radius and mitigation

Show the three downstream assets. Then show the shadow mitigation: suppress birth date,
which changes this synthetic fixture from `k=1` to `k=20` without touching source data.

## 1:30â€“1:55 â€” Prove it is not a toy

Show the safe controls and graph-value comparison: generalized export clears; direct
PII is deliberately not mislabeled as a compositional finding; baseline finds zero
cross-source convergences while Mosaic finds one.

## 1:55â€“2:25 â€” Catalog memory

Run the live evidence command. Show DataHub lineage reread, DuckDB aggregate proof,
and approved tag/Document write-back reread. Close with: â€œMosaic turns a hidden
connection into a reviewable privacy decision that the next human or agent inherits.â€
