# Generated remediation examples

These directories are exact outputs from Mosaic's metadata-aware code generator:

- `research-remediation/` suppresses precise birth date from a research export.
- `audience-remediation/` generalizes neighborhood and suppresses household size.

Each example contains a dbt model, dbt schema, aggregate-only singular test,
privacy policy, provenance manifest, and reviewer-ready PR summary. The generator
embeds the source DataHub URN, scenario digest, lineage, downstream review boundary,
and per-file SHA-256 receipts.

Regenerate both examples:

```powershell
uv run mosaic generate-remediation --scenario research --output examples/generated/research-remediation
uv run mosaic generate-remediation --scenario audience --output examples/generated/audience-remediation
```

Generated outputs are proposals. Mosaic does not commit, merge, execute, or publish
them without human review.
