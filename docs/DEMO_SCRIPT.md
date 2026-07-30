# Mosaic demo - 2:40 target

## 0:00-0:20 - Make the risk intuitive

Open the landing page. Say: "No column here is PII. Together, they identify you." Explain minimum k in one sentence: it is the size of the smallest crowd a record blends into. k=1 means a unique combination. Scroll through Impact and name the outcome: prevent exposure, contain blast radius, preserve utility, and retain the decision.

## 0:20-0:45 - Show that the demos are real

Choose the critical research preset, then the mitigated and control presets. Point out that each changes the backend scenario hash, query, exact metrics, verdict, and downstream count. Return to the research case and start the guided analysis.

## 0:45-1:15 - Show why DataHub matters

Pause on the DataHub architecture section: the product names seven used surfaces—fine-grained lineage, downstream graph, Python SDK, GraphQL, MCP Server, DataHub Skill, and governed write-back—and links each claim to code or a proof receipt. Then follow ZIP5, birth date, and demographic category from separate systems into one research export. A table scanner sees harmless columns; DataHub reveals where they converge and who inherits the risk.

## 1:15-1:40 - Validate without exposing anyone

Open the query tab. Show the allow-listed `GROUP BY COUNT(*)` query, then minimum k=1, 100% below k=5, and raw rows returned=0. Say: "Mosaic measures group sizes. It never asks who is in a group."

## 1:40-2:00 - Turn a finding into a decision

Open mitigation. Show that the shadow strategy reaches minimum k=20 without changing the source. Open DataHub proposal and stress that it is a dry run until a human approves it.

## 2:00-2:25 - Prove breadth and honesty

Open Evidence. Mention the 48-case exactness benchmark, hash-verified DataHub replay, and aggregate-only UCI Adult proof: 32,561 records processed in memory, minimum k moving from 43 to 1 when ordinary attributes compose, and no raw rows committed. State clearly that the benchmark is regression evidence, not field accuracy.

## 2:25-2:40 - Close the loop

Open a retained run detail page locally or the current proof on the hosted page. Show the SHA-256 integrity state, printable report, and provenance. Close with: "Mosaic turns a hidden graph connection into a reviewable privacy decision that the next human or agent inherits."

## Backup judge commands

```powershell
uv sync --locked --extra dev
uv run mosaic assess --scenario research
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
uv run mosaic serve
```

The critical assessment and estate scan intentionally return exit code 3. That is a policy result, not an application crash.