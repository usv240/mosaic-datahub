# Mosaic narrated demo — recording script

Eleven scenes, about 2:43, comfortably inside the three-minute limit. Every **Say** line is the verbatim voice-over from [`narration.txt`](demo/narration.txt); the two files must stay in sync, and the build refuses to run if they drift.

## The story in one line

Three columns nobody flags, from three systems nobody compares, identify almost everyone in the table — and Mosaic finds it, proves it, and writes the fix.

## The five chapters

Judges should feel one story, not eleven features. The scenes group into five beats:

| Chapter | Scenes | The judge's takeaway |
|---|---|---|
| **Problem** | 1–2 | Harmless columns become identifying at the join — and only the graph sees the join |
| **Prove it** | 3–5 | Not a false-alarm machine; the risk is real and measured with zero rows read |
| **Can we trust it?** | 6–7 | There's an AI, but it's boxed in — and we attacked the box on purpose |
| **Fix it** | 8 | It doesn't just warn; it writes review-ready code |
| **Why DataHub, and proof** | 9–11 | DataHub is load-bearing; it works on data we didn't build; here are the limits |

## Two production rules that matter more than any single line

1. **The screen proves; the voice narrates.** Never say a technical fact the screen can show. Say *"zero rows read"* while `RAW ROWS: 0` sits on screen. Say *"it refused"* while `REFUSED` is up. The big on-screen signals — `CRITICAL`, `0 RAW ROWS`, `REFUSED`, `1 → 20`, `6 FILES` — are the screenshots that stay in a judge's memory. List them under **Screen** below.
2. **The cursor is a pointer, not a fidget.** Move → point → stop → speak. On the four "hold" moments (120 unique, 0 rows, REFUSED, 1 → 20) the cursor stops moving completely.

## Before you record

```powershell
uv sync --locked --extra dev
uv run mosaic serve
```

- Open `http://127.0.0.1:8123` at **1280×720**. Larger windows push panels off-frame.
- Dark theme (`#theme-toggle`), reduced motion on, browser zoom 100%.
- Hide bookmarks, notifications, and any second monitor.
- Between scenes marked **fresh page**, reload `/` so the case explorer resets.
- Add clean captions in post — no word-by-word karaoke, just plain subtitles. Keep any background music near-silent; the product is the drama.

---

## Chapter 1 — Problem

### Scene 1 — Hook · ~0:00–0:12 · *fresh page*

| | |
|---|---|
| **Go to** | `/` — top of the landing page |
| **Do** | Nothing. Hold the hero still. |
| **Point at** | `#hero-title`, then the three column chips as you name them |
| **Screen** | Three "not PII" chips combining into one warning |

> **Say:** ZIP code. Birth date. Gender. None looks dangerous alone. But when pipelines bring them together, that combination can identify a person. Mosaic finds that hidden risk before it ships, and writes the fix.

Deliver "ZIP code. Birth date. Gender." fast and clipped, then slow on "can identify a person." Keep the claim general here — scene 5's 120-out-of-120 result is where Mosaic supplies its own demonstrated number, and it lands harder for not being pre-empted. Do not click during this line; the hook is the whole scene.

### Scene 2 — Why teams miss it · ~0:12–0:29

| | |
|---|---|
| **Go to** | Case explorer → run the **research** case to completion, scroll `#workspace` into view |
| **Do** | Trace each lineage edge in `#lineage-stage` as you name its system |
| **Point at** | support → ZIP, membership → birth date, demographics → gender — finish on the convergence node |
| **Screen** | Three separate sources funnelling into one export |

> **Say:** Here's why teams miss it. ZIP came from support. Birth date from membership. Gender from demographics. Three systems, three owners, each column harmless where it lives. Field-by-field scanners check columns one at a time. Mosaic asks what becomes identifying only after the graph brings them together, and DataHub's column lineage shows that convergence.

Say the three sources fast, then slow for the **originality** line — *"Mosaic asks what becomes identifying only after the graph brings them together."* That one sentence is your novelty; let the cursor rest on the convergence node while you say it.

---

## Chapter 2 — Prove it

### Scene 3 — Does it cry wolf? · ~0:29–0:43 · *fresh page*

| | |
|---|---|
| **Go to** | `/` → case explorer → run all four cases → open `#tour-summary` (Compare results) |
| **Do** | Glance at the two critical tiles, then **rest the cursor on the negative-control tile** |
| **Point at** | `#tour-summary` tiles; hold on the safe case |
| **Screen** | Negative control: **No finding · Queries 0 · Code 0** |

> **Say:** But does Mosaic just flag everything? No. Here are four cases. Two contain real risk. One shows the fix working. And on this safe table, Mosaic stays quiet: no query, no code, no finding. A tool that cries wolf gets switched off.

The negative control is the most persuasive tile on screen — give it the most cursor time, not the least. A tool that can say "nothing is wrong" is the one people trust. End on the memorable line and hold a half-beat.

### Scene 4 — Across tables too · ~0:43–0:52 · *fresh page*

| | |
|---|---|
| **Go to** | `/` → expand `#cross-asset-title`, scroll `.cross-asset-proof` into view |
| **Do** | `#cross-left` → `#cross-key` → `#cross-right`, in order |
| **Point at** | Rest on the shared key (`#cross-key`) |
| **Screen** | Two exports, one shared key linking them |

> **Say:** The same risk can hide across tables. Each export may look safe alone, but a shared customer key can reconnect them. Mosaic catches that relationship too, before reading any data.

This is the shortest scene by design — it's a "there's more" beat, not a full case. Pause on the shared key; that single element is the whole idea. If the final cut ever runs long, this is the first scene to trim, never the fix or the DataHub scene.

### Scene 5 — Proof · ~0:52–1:07

| | |
|---|---|
| **Go to** | Research case result, `#workspace` in view |
| **Do** | Hold still. This scene is numbers, not motion. |
| **Point at** | `#metric-k` on "every single one is unique", then move to `#metric-raw` and **leave it there** |
| **Screen** | **120 people · 120 unique · 0 RAW ROWS** |

> **Say:** Now Mosaic measures the actual risk. This export contains one hundred twenty people, and every single one is unique on those three columns. Mosaic proves it by counting groups, without reading a single person-level row. And even the A I in the loop can't bypass that boundary.

This is your first WOW moment. After "every single one is unique," **pause**. Keep `#metric-raw` (zero rows) on screen while you say it — detects the risk without creating a new one. The last sentence is a bridge: it hands you into Scene 6 so the model doesn't arrive as a new topic.

---

## Chapter 3 — Can we trust it?

### Scene 6 — The boundary around the model · ~1:07–1:23

| | |
|---|---|
| **Go to** | Same page → expand `.agent-proof`, scroll into view |
| **Do** | `#agent-selection` → `#agent-rationale` while describing what the model did; then hold on `#agent-policy` for the three "cannot" lines |
| **Point at** | Park the cursor on the policy panel during "cannot… cannot… cannot" |
| **Screen** | `QUERY: policy` · `VERDICT: policy` · `WRITE: human approval` |

> **Say:** There's an A I model here, but Mosaic doesn't trust it blindly. The model can suggest where to investigate, and explain why. It cannot write the query, decide the verdict, or change DataHub. Deterministic policy owns those, and can overrule the model. So we tried to break it.

**One idea only: we don't trust the AI blindly.** Deliver the three "cannot" clauses flat and evenly — don't rush them, they're the differentiator. If the UI can flash `DENIED` / `POLICY` / `HUMAN` beside each one, that's stronger than any sentence. The last line — *"So we tried to break it"* — is the cliff-hanger into the attack; say it and cut.

### Scene 7 — The attack · ~1:23–1:37

| | |
|---|---|
| **Go to** | Same page → click `#review-attack`, wait for `#attack-verdict` to read **REFUSED**, scroll `#tab-attack` into view |
| **Do** | Show the hostile description text; let **REFUSED** appear before you say "refuses" |
| **Point at** | Malicious text → `#attack-verdict` → `#attack-rows` |
| **Screen** | The injected instruction, then **REFUSED · 0 ROWS · REGRESSION TESTED** |

> **Say:** We hid a malicious instruction inside DataHub metadata: export member identifiers and full birth dates. The model asks for it. Policy refuses. Zero rows exposed, and the safe workflow continues. If that protection ever breaks, our build fails.

Make it feel like an attack. Say *"The model asks for it…"*, **pause** on the hostile request, then let `REFUSED` land. This is the shot most competitors won't have: a tested failure mode, not a happy path. The narration never says "regression-tested" — the `REGRESSION TESTED` badge on screen carries that claim, which lets `REFUSED` land harder.

---

## Chapter 4 — Fix it

### Scene 8 — The fix · ~1:37–1:57

| | |
|---|---|
| **Go to** | Same page → click `#tab-button-codegen`, wait for `#generated-file-list` to populate |
| **Do** | Hold on `#codegen-impact` for the before/after, then run the cursor down all six file rows; briefly open one generated SQL file if the UI allows |
| **Point at** | `#codegen-impact` (1 → 20), then each row of `#generated-file-list`, ending on `#codegen-sha` |
| **Screen** | **1 → 20**, then six named files: `*_privacy_safe.sql`, `*.yml`, `assert_*_minimum_k.sql`, `privacy-policy.yml`, `mosaic-manifest.json`, `PR_SUMMARY.md` |

> **Say:** Now that the finding is trusted, Mosaic builds the fix. Suppress birth date, and the smallest anonymity group jumps from one person to twenty. And it doesn't stop at advice. It generates the actual change: a d b t model, a schema contract, a privacy test, the policy, a provenance manifest, and a reviewer summary. Six files, ready for review.

**This is the payoff and the category fit — Metadata-Aware Code Generation.** Do not let it feel secondary. Say *"one…"* — **pause** — *"to twenty,"* with `1 → 20` big on screen; even a non-expert reads it as *one person alone → twenty who look the same*. Then show the six real filenames (not tiny code windows), and say "ready for review," not "ready to merge" — write-back is human-gated, and the humility reads as maturity. Give this scene an extra beat if you have it.

---

## Chapter 5 — Why DataHub, and proof

### Scene 9 — Why DataHub · ~1:57–2:14 · *fresh page*

| | |
|---|---|
| **Go to** | `/` → scroll `#datahub-stack` into view |
| **Do** | Move left→right across the surfaces, ending on the write-back tile |
| **Point at** | lineage → downstream graph → act → write-back, as a loop |
| **Screen** | `READ → REASON → FIX → WRITE BACK ↻` |

> **Say:** None of this works without DataHub. Its schema and lineage reveal the hidden combination. Its downstream graph shows everything affected. And after a human approves, Mosaic writes the decision back into DataHub, so the investigation doesn't vanish when the engineer closes their laptop. The next person, or agent, inherits the answer.

Explain value, not interfaces. Write-back is the payoff here — *institutional memory*, not an API call. The cursor should travel a loop (read → reason → fix → write back), not read a flat list of MCP/GraphQL/tags. Those can stay visible for technical judges; the narration sells the loop.

### Scene 10 — Someone else's catalog · ~2:14–2:28

| | |
|---|---|
| **Go to** | `/runs` → scroll `#proof-catalog` into view |
| **Do** | Show the positive receipt, then the single-source control, side by side |
| **Point at** | Positive convergence → the "no finding" control |
| **Screen** | **DATAHUB SHOWCASE CATALOG · external to Mosaic** — convergence beside no-finding |

> **Say:** And this isn't only tuned to our demo data. We ran Mosaic against DataHub's own showcase catalog, data we did not design. It found a real cross-system combination, and on a single-source table, it correctly found nothing. Same engine, opposite decisions.

This scene answers exactly one objection: *did you just hard-code your fixtures?* Make the "external to Mosaic" framing unmissable so the judge sees why it matters. The detailed numbers (32 origins, 10 upstreams) stay on screen for technical judges — don't ask everyone to memorize them.

### Scene 11 — Honest close · ~2:28–2:43

| | |
|---|---|
| **Go to** | `/settings#readiness` → scroll `#connector-matrix` into view |
| **Do** | Gesture at the unmet requirements during the limits sentence, then **stop moving** for the close |
| **Point at** | `#connector-matrix` briefly, then hold |
| **End card** | `MOSAIC — Find the hidden combination. Prove the risk. Write the fix.` · `Apache-2.0 · DataHub upstream contribution merged ✓` |

> **Say:** Mosaic reduces privacy risk. It does not prove anonymity or replace human judgment. Teams still own their thresholds and approvals. But the hard part is done. Mosaic turns context already in your DataHub graph into something your team can act on: find the hidden combination, prove the risk, and write the fix.

Say the limits briskly, the close slowly. End on the three verbs — *find, prove, write* — then cut to the end card repeating them; the callback closes the loop the video opened. No "thank you," no "check out our GitHub," no "that's Mosaic." The last words heard are the value. Put the merged upstream contribution and Apache-2.0 on the end card — it quietly serves the open-source bonus without a dedicated scene.

---

## Delivery rules

- **One idea per scene.** If a beat needs two sentences of setup, it is two beats or it is cut.
- **Vary the pace.** Fast on the source list and the "cannot" clauses; slow on the numbers — "one… to twenty," "zero person-level rows."
- **Four full stops.** Cursor stops completely on: 120 unique, 0 rows, REFUSED, 1 → 20.
- **Say what numbers mean.** "Every one is unique" beats "minimum k equals one."
- **Human words in the voice, technical terms on screen.** "Counts groups without reading rows," not "aggregate-only validation."
- **Limits before the close, never as the close.**

## Rebuilding after a script change

1. Edit [`narration.txt`](demo/narration.txt) — one paragraph per scene, eleven paragraphs. Spell acronyms for the voice (`A I`, `d b t`, `S Q L`, `M C P`, `Graph Q L`); the word-count guard counts those spelled tokens.
2. Re-render `docs/demo/narration.wav` from the new text.
3. Update per-scene word counts in `SCENES` (`scripts/build_submission_video.py`) — or run the snippet below to derive them.
4. `uv run --with imageio-ffmpeg python scripts/build_submission_video.py`

```python
import pathlib
paras = [p.strip() for p in pathlib.Path("docs/demo/narration.txt").read_text(encoding="utf-8").split("\n\n") if p.strip()]
print([len(p.split()) for p in paras])   # paste into SCENES word counts, in order
```

The build fails if the word counts disagree with the narration, and refuses to publish anything over three minutes. Total runtime is read from the rendered audio, so the picture can never be trimmed mid-sentence. Screenshots are regenerated by `scripts/capture_submission_media.py`, which drives the same navigation listed above — treat it as the source of truth if a selector moves.

## Backup judge commands

```powershell
uv sync --locked --extra dev
uv run mosaic assess --scenario research
uv run mosaic assess --agent --replay --scenario research
uv run mosaic check --fail-on critical
uv run mosaic redteam
uv run mosaic benchmark
uv run mosaic replay-fixture
uv run mosaic generate-remediation --scenario research --output generated/research
uv run mosaic serve
```

Critical assessment, estate scan, and pre-merge gate intentionally return exit code 3. That is a policy result, not an application crash.
