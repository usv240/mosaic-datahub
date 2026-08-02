# Judge path

## One-command product review

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

Open `http://127.0.0.1:8123` and choose **Watch all 4 decisions (30 sec)**. The presenter run proves two detected risks, one verified mitigation, one refused false positive, and zero person-level rows, then brings its comparison scorecard into view automatically. For a technical deep dive, select Research export and inspect Finding, Validation query, Attack lab, Mitigation lab, Remediation PR, and DataHub proposal in order. Light/dark themes, retained run history, printable integrity-verified evidence, and guarded operator settings are also included.

## Offline proof commands

```powershell
uv run mosaic assess --scenario research
uv run mosaic scan
uv run mosaic benchmark
uv run mosaic replay-fixture
```

Critical policy results exit 3. The benchmark and replay exit zero only when their checks pass.

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