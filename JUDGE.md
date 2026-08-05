# Judge path

## One-command product review

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

Open `http://127.0.0.1:8123` and choose **Choose one of 4 demos**. Open the case explorer, select a case, and press **Start selected case**. Step 1 appears; each press of **Continue** reveals exactly one later evidence step. Waiting does nothing. Use **Next case** and **Compare results** only when ready. The four cases prove two detected risks, one verified mitigation, one refused false positive, and zero person-level rows. For a technical deep dive, inspect Finding, Validation query, Attack lab, Mitigation lab, Remediation PR, and DataHub proposal before moving next. Light/dark themes, retained run history, printable integrity-verified evidence, and guarded operator settings are also included.

## Offline proof commands

```powershell
uv run mosaic assess --scenario research
uv run mosaic assess --agent --replay --scenario research
uv run mosaic assess --agent --replay fixtures/agent_transcripts/vetoed.json --scenario research
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
```

Critical policy results exit 3. The benchmark and replay exit zero only when their checks pass.

The two `--replay` commands need no model runtime, API key, or network access. Each returns a digest-verified recording of a real local-model proposal — the first was accepted for human review, the second was vetoed by policy for nominating a single quasi-identifier — and both run the same parsing, verification, and veto code as a live call. If a transcript is edited, the digest check fails closed rather than replaying altered content.

## Strongest local integration proof

With disposable DataHub Core at `http://localhost:8080`:

```powershell
uv sync --locked --extra dev --extra datahub
uv run mosaic live-demo --server http://localhost:8080
uv run mosaic live-demo --server http://localhost:8080 --approve-writeback
```

The first command is dry-run. The second creates uniquely named synthetic assets, verifies fine-grained lineage and downstream reach, runs exact DuckDB aggregates with zero raw rows, publishes a field tag, structured property, threat-model Document, and incident, and re-reads each mutation.

## What not to overclaim

The 48-case benchmark is bounded regression evidence. The versioned recording is not a live server. The UCI Adult artifact is a historical composition-mechanism check, not current prevalence. Thresholds are demo policy rather than law. Mosaic makes each limitation visible in its artifacts and submission narrative.