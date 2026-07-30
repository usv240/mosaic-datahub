from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mosaic.models import Assessment, Candidate, Verdict
from mosaic.query_policy import aggregate_query, validate_aggregate_query
from mosaic.risk import exact_k_metrics

SPEC_ROOT = Path(__file__).with_name("scenario_specs")


@dataclass(frozen=True)
class ScenarioSpec:
    slug: str
    name: str
    domain: str
    situation: str
    asset: str
    asset_urn: str
    columns: tuple[str, ...]
    column_types: tuple[tuple[str, str], ...]
    families: tuple[str, ...]
    lineage_paths: tuple[tuple[str, ...], ...]
    downstream_assets: tuple[str, ...]
    class_sizes: tuple[int, ...]
    candidate: bool
    mitigation: dict[str, Any] | None
    source_systems: tuple[str, ...]
    config_sha256: str


def _load(path: Path) -> ScenarioSpec:
    raw = path.read_bytes()
    data = json.loads(raw)
    return ScenarioSpec(
        slug=data["slug"],
        name=data["name"],
        domain=data["domain"],
        situation=data["situation"],
        asset=data["asset"],
        asset_urn=data["asset_urn"],
        columns=tuple(data["columns"]),
        column_types=tuple(data["column_types"].items()),
        families=tuple(data["families"]),
        lineage_paths=tuple(tuple(path) for path in data["lineage_paths"]),
        downstream_assets=tuple(data["downstream_assets"]),
        class_sizes=tuple(data["class_sizes"]),
        candidate=bool(data["candidate"]),
        mitigation=data.get("mitigation"),
        source_systems=tuple(data["source_systems"]),
        config_sha256=hashlib.sha256(raw).hexdigest(),
    )


def list_scenarios() -> list[ScenarioSpec]:
    return [_load(path) for path in sorted(SPEC_ROOT.glob("*.json"))]


def get_scenario(slug: str) -> ScenarioSpec:
    if not slug or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in slug
    ):
        raise KeyError(slug)
    path = SPEC_ROOT / f"{slug}.json"
    if not path.is_file():
        raise KeyError(slug)
    return _load(path)


def _aggregate_fixture(spec: ScenarioSpec) -> tuple[dict[str, str], ...]:
    """Expand class sizes into synthetic keys; no identity-bearing values are created."""
    return tuple(
        {column: f"class-{class_index}-{column}" for column in spec.columns}
        for class_index, size in enumerate(spec.class_sizes)
        for _ in range(size)
    )


def assess_scenario(slug: str) -> dict[str, Any]:
    spec = get_scenario(slug)
    candidate = Candidate(
        asset_urn=spec.asset_urn,
        columns=spec.columns,
        families=spec.families,
        lineage_paths=spec.lineage_paths,
        sensitive_attribute_present=spec.candidate,
        downstream_assets=spec.downstream_assets,
    )
    query = None
    metrics = None
    if spec.candidate:
        query = aggregate_query(spec.asset, spec.columns)
        validate_aggregate_query(query, spec.asset, spec.columns)
        metrics = exact_k_metrics(_aggregate_fixture(spec), spec.columns)
        if metrics.minimum_k < 2 and metrics.percent_below_5 >= 20:
            verdict = Verdict.VALIDATED_CRITICAL
        elif metrics.minimum_k >= 5 and metrics.percent_below_5 == 0:
            verdict = Verdict.VALIDATED_LOW
        else:
            verdict = Verdict.VALIDATED_ELEVATED
        reasons = (
            f"{len(set(spec.families))} quasi-identifier families converge across "
            f"{len(spec.source_systems)} source systems.",
            f"Aggregate-only validation found minimum k={metrics.minimum_k} and "
            f"{metrics.percent_below_5:.3f}% of records below k=5.",
            f"DataHub lineage identifies {len(spec.downstream_assets)} downstream assets.",
        )
    else:
        verdict = Verdict.SCREENING_ONLY
        reasons = (
            "Metadata screening found no multi-family person-joinable convergence.",
            "No aggregate data query was issued.",
            "High cardinality alone is not treated as compositional privacy risk.",
        )
    assessment = Assessment(
        candidate=candidate,
        verdict=verdict,
        reasons=reasons,
        metrics=metrics,
        aggregate_query=query,
        raw_rows_returned=0,
        mitigation=spec.mitigation,
    )
    graph_only = spec.candidate and len(spec.source_systems) > 1
    return {
        "schema_version": 1,
        "scenario": {
            "slug": spec.slug,
            "name": spec.name,
            "domain": spec.domain,
            "situation": spec.situation,
            "configuration_sha256": spec.config_sha256,
        },
        "assessment": assessment.to_dict(),
        "graph_value": {
            "lineage_aware_convergences": 1 if graph_only else 0,
            "no_lineage_baseline_convergences": 0,
            "delta": 1 if graph_only else 0,
            "source_systems": list(spec.source_systems),
        },
        "writeback": {
            "status": "dry_run",
            "requires_reviewer_approval": True,
            "target_urn": spec.asset_urn,
            "mutation_performed": False,
        },
        "source": {
            "kind": "configuration_driven_synthetic_fixture",
            "raw_person_rows_returned": 0,
        },
        "exit_code": assessment.exit_code,
    }
