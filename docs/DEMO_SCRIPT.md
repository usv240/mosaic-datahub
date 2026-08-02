# Mosaic narrated demo — 2:49

The committed MP4 is generated from these eleven tested 16:9 scenes and the exact voice-over in [`narration.txt`](demo/narration.txt). Rebuild it with `uv run --with imageio-ffmpeg python scripts/build_submission_video.py` after capturing media.

## 0:00–0:10 — The claim

Show the first viewport: Mosaic finds privacy risk that appears only when individually harmless columns combine across pipelines, then generates a review-ready fix grounded in DataHub context.

## 0:10–0:23 — The core lineage example

Show ZIP code, birth date, and demographic category arriving through independent column-lineage paths. Point out that the fields are not direct identifiers and that DataHub reveals both their origins and downstream exposure.

## 0:23–0:36 — Four decisions, not one rehearsed answer

Show the presenter scorecard: two critical findings, one verified mitigation, and one negative control that produces no query or code. State that all four cases return zero person-level rows.

## 0:36–0:51 — Cross-asset composition

Show the join detector. Two assets can look ordinary alone while a shared entity key makes their combined context risky. Keep the boundary explicit: metadata screens candidates; only aggregate validation earns a verdict.

## 0:51–1:03 — Measured evidence

Show the research result: smallest group of one, every group below the five-person demo target, three downstream assets, and zero raw rows. Explain that the graph selects where to measure.

## 1:03–1:22 — Model proposes, policy disposes

Show the recorded local-model proposal and deterministic policy boundary. The model may select an allowlisted asset, nominate columns, and draft rationale; it cannot write SQL, calculate the verdict, or mutate DataHub. Mosaic can veto it.

## 1:22–1:36 — Prompt-injection refusal

Show hostile instructions embedded in DataHub metadata requesting identifiers and full birth dates. The query policy refuses the request, records the reason, returns zero rows, and continues safely.

## 1:36–1:52 — Merge-ready remediation

Show the six-file bundle: dbt model, enforced schema contract, aggregate test, policy snapshot, provenance manifest, and PR summary. Every artifact retains DataHub context and human review.

## 1:52–2:08 — DataHub is the substrate

Show the seven DataHub surfaces: schema, fine-grained lineage, downstream impact, SDK, GraphQL, MCP, Skill, and governed write-back. Mention that reviewed decisions are re-read and preserved for the next human or agent.

## 2:08–2:28 — Positive and negative external proof

Show the evidence catalog. The official DataHub showcase asset produces a multi-source convergence while the single-source control correctly produces no finding. Mention the merged upstream DataHub contribution.

## 2:28–2:50 — Production boundary and close

Show readiness requirements and the honest Snowflake credential block. Close with: Mosaic is privacy-risk reduction, not proof of anonymity or legal compliance; production still requires organization policy, least-privilege identities, SSO/RBAC, compatibility validation, and human approval.

## Backup judge commands

```powershell
uv sync --locked --extra dev
uv run mosaic discover --server http://localhost:8080 --urn "<existing-sample-urn>"
uv run mosaic assess --scenario research
uv run mosaic check --fail-on critical
uv run mosaic redteam
uv run mosaic benchmark
uv run mosaic replay-fixture
uv run mosaic generate-remediation --scenario research --output generated/research
uv run mosaic serve
```

Critical assessment, estate scan, and pre-merge gate intentionally return exit code 3. That is a policy result, not an application crash.