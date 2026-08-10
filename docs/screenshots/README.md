# Mosaic product gallery

Light-mode captures taken from the deployed console at
<https://mosaic-datahub-production.up.railway.app>. The console also ships a dark theme;
CI verifies accessibility in both.

## Four decisions, one engine

Two detected risks, one verified mitigation, and one refused false positive. The negative
control is the important one: Mosaic produces no query and no code when the evidence is not
there.

[![Four cases, four evidence-based decisions](light-06-four-case-scorecard.png)](light-06-four-case-scorecard.png)

## Guided investigation

DataHub column lineage on the left showing where three families converge, aggregate-only
metrics on the right. Raw person-level rows returned is fixed at zero.

[![Live investigation with lineage convergence and aggregate metrics](light-02-investigation.png)](light-02-investigation.png)

## Merge-ready remediation PR

All six generated artifacts, the measured `k=1 -> k=20` result, the DataHub URN embedded in
the SQL, and the retained human review gate.

[![Metadata-aware remediation PR studio](light-03-remediation.png)](light-03-remediation.png)

## Prompt-injection refusal

A hostile instruction hidden in a DataHub dataset description asks for person-level
identifiers. The deterministic query policy refuses it and the safe run continues.

[![Metadata prompt injection refused with zero raw rows](light-04-attack-refusal.png)](light-04-attack-refusal.png)

## Measure your own file

The bring-your-own-data panel runs entirely in the browser. The file is never uploaded and
the output is counts only, because the equivalence-class values are themselves the
identifier.

[![Browser-side measurement with zero values sent to the server](light-05-your-own-data.png)](light-05-your-own-data.png)

## Landing page

[![Mosaic landing page](light-01-hero.png)](light-01-hero.png)

---

Regenerate these with `scripts/capture_submission_media.py`. Narrated-video stills live in
`artifacts/submission-media/`, and `docs/demo/media-manifest.json` records byte lengths and
SHA-256 digests.
