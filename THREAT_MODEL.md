# Threat model

## Protected asset

The fictional `research_export_clean` dataset has no direct identifier, but contains
derived ZIP5, birth date, and gender attributes. Its risk comes from their joint
equivalence classes and its downstream research/partner use.

## Attacker model

An authorized recipient may possess compatible auxiliary facts. Mosaic does **not**
join auxiliary person-level data or attempt a match; it measures whether the released
combination has small anonymity sets and requires a reviewer to assess context.

## Controls

1. Fine-grained lineage establishes how fields converged.
2. A policy validator permits only approved count aggregates.
3. Raw rows are not returned to the agent or UI.
4. Mitigations are simulated in memory and are never applied automatically.
5. Planned DataHub write-back is approval-gated and must re-read the exact target
   asset after mutation.
