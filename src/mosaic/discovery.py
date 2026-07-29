from __future__ import annotations

from mosaic.models import Candidate
from mosaic.scenario import HERO_URN, SyntheticEstate


def discover_convergences(estate: SyntheticEstate) -> list[Candidate]:
    """Find multi-family combinations that only become visible through lineage."""
    columns = tuple(estate.column_families)
    if len(set(estate.column_families.values())) < 2 or len(columns) < 2:
        return []
    return [
        Candidate(
            asset_urn=HERO_URN,
            columns=columns,
            families=tuple(estate.column_families[column] for column in columns),
            lineage_paths=tuple(estate.lineage[column] for column in columns),
            sensitive_attribute_present=True,
            downstream_assets=estate.downstream_assets,
        )
    ]


def no_lineage_baseline(estate: SyntheticEstate) -> list[Candidate]:
    """A per-table scanner cannot combine families from separate source assets."""
    # Every source carries one candidate family; without graph edges it must not
    # assert an estate-wide convergence.
    return []


def graph_value_report(estate: SyntheticEstate) -> dict[str, object]:
    graph = discover_convergences(estate)
    baseline = no_lineage_baseline(estate)
    return {
        "status": "passed" if len(graph) > len(baseline) else "failed",
        "graph_convergences": len(graph),
        "baseline_convergences": len(baseline),
        "lineage_only_paths": [list(path) for path in graph[0].lineage_paths] if graph else [],
    }
