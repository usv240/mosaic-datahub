# Mosaic

> No column here is PII. Together, they identify you.

**[Open the read-only live demo](https://mosaic-datahub-production.up.railway.app)**

Mosaic is a privacy threat-modeling agent for the risk that emerges when ordinary
attributes converge across a data estate. It uses DataHub column lineage to find the
convergence, validates the resulting anonymity-set risk with an approved aggregate-only
query, traces downstream exposure, and proposes a reversible mitigation for reviewer
approval.

This repository is intentionally separate from Hindsight. Hindsight protects ML
releases from temporal leakage; Mosaic protects research-data sharing from compositional
privacy exposure.

## What works now

Mosaic now provides a deterministic offline judge path and a verified synthetic live
DataHub workflow:

- a synthetic healthcare-research fixture with no direct identifiers;
- lineage-aware discovery of ZIP5 + birth date + gender convergence;
- an explicit no-lineage baseline which cannot find that cross-source convergence;
- exact equivalence-class (`k`) metrics, calculated internally and released only as
  aggregates;
- a strict query-policy validator that rejects joins, filters, extra projections,
  mutations, and multiple statements;
- three shadow mitigation alternatives with measured privacy/utility tradeoffs;
- retained SHA-256 evidence records and downloads; and
- approval-gated DataHub tag, property, Document, and incident write-back with rereads.

The current fixture deliberately produces a critical result: all 120 synthetic records
are in `k=1` classes for the three-field combination. Suppressing birth date leaves six
ZIP5/gender groups of twenty. These are fixture facts, not universal privacy thresholds
or claims about real people.

## Judge quick start

```powershell
uv sync --extra dev
uv run mosaic demo
```

The command requires no network, Docker, DataHub server, warehouse, LLM, or real data.
It produces a JSON evidence bundle and returns `3` because the fixture's validated risk
is intentionally critical. Exit `3` is the assessment result, not a software failure.

To open the judge-facing privacy console (light/dark mode, evidence graph, and mitigation story):

```powershell
uv run mosaic serve
``` 

Then open `http://127.0.0.1:8123`. The console consumes the same deterministic evidence bundle as the CLI. 

To run the tests:

```powershell
uv run pytest
```

## Why DataHub is essential

A single-table PII scanner sees separate harmless-looking fields. It cannot establish
that a research export inherited location from one system, birth date from another, and
demographics from a third. The live workflow retrieves fine-grained paths and downstream blast radius from DataHub,
executes exact aggregates in DuckDB, and writes an approved threat-model Document,
structured risk property, tag, and incident. Official MCP search, column lineage, mutation,
and reread are verified.

The offline fixture makes the central claim testable now: `graph_value` reports one
lineage-only convergence and zero baseline discoveries, including the exact lineage
edges responsible. It is not sufficient that an authored graph exists; the comparative
delta is part of the demo output.

## Safety boundary

Mosaic never attempts to identify a person. It uses deterministic synthetic records,
returns zero person-level rows to the agent/UI, and accepts only one allowlisted
`GROUP BY ... COUNT(*)` query shape. The results are privacy-engineering evidence for a
reviewer—not a legal determination or a license to process personal data.

See [ETHICS.md](ETHICS.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

## Verification status

The locked standalone environment passes tests, lint, formatting, the complete live workflow,
and official MCP proof. Fresh-edge fine-grained Agent Context Kit resolution was not
reliable on the pinned local version, so Mosaic uses the verified SDK and MCP column-path
surfaces and states that limitation explicitly.