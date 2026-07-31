from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mosaic.canonical import canonical_json_sha256
from mosaic.mitigation import simulate_mitigation
from mosaic.models import Assessment, Candidate, Verdict
from mosaic.policy import load_policy
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
    join_keys: tuple[str, ...]
    columns: tuple[str, ...]
    column_types: tuple[tuple[str, str], ...]
    families: tuple[str, ...]
    lineage_paths: tuple[tuple[str, ...], ...]
    downstream_assets: tuple[str, ...]
    row_generator: dict[str, Any]
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
        join_keys=tuple(data.get("join_keys", ())),
        columns=tuple(data["columns"]),
        column_types=tuple(data["column_types"].items()),
        families=tuple(data["families"]),
        lineage_paths=tuple(tuple(path) for path in data["lineage_paths"]),
        downstream_assets=tuple(data["downstream_assets"]),
        row_generator=data["row_generator"],
        candidate=bool(data["candidate"]),
        mitigation=data.get("mitigation"),
        source_systems=tuple(data["source_systems"]),
        config_sha256=canonical_json_sha256(data),
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


def generate_rows(spec: ScenarioSpec) -> tuple[dict[str, str], ...]:
    """Generate deterministic fictional rows from domains, never precomputed class sizes."""
    config = spec.row_generator
    count = int(config.get("count", 0))
    seed = int(config.get("seed", 0))
    fields = config.get("fields", {})
    if count < 1 or set(fields) != set(spec.columns):
        raise ValueError(f"invalid row generator for scenario {spec.slug}")
    randomizer = random.Random(seed)
    rows: list[dict[str, str]] = []
    for index in range(count):
        row: dict[str, str] = {}
        for column in spec.columns:
            field = fields[column]
            domain = tuple(str(value) for value in field.get("domain", ()))
            if not domain:
                raise ValueError(f"empty row-generator domain for {column}")
            distribution = field.get("distribution", "cycle")
            if distribution == "cycle":
                position = index * int(field.get("stride", 1)) + int(field.get("offset", 0))
                row[column] = domain[position % len(domain)]
            elif distribution == "uniform":
                row[column] = randomizer.choice(domain)
            elif distribution == "weighted":
                weights = field.get("weights")
                if not isinstance(weights, list) or len(weights) != len(domain):
                    raise ValueError(f"invalid weights for {column}")
                row[column] = randomizer.choices(domain, weights=weights, k=1)[0]
            else:
                raise ValueError(f"unsupported distribution for {column}: {distribution}")
        rows.append(row)
    return tuple(rows)


def assess_scenario(slug: str) -> dict[str, Any]:
    spec = get_scenario(slug)
    policy = load_policy()
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
        rows = generate_rows(spec)
        metrics = exact_k_metrics(rows, spec.columns)
        if (
            metrics.minimum_k < policy.critical_minimum_k
            and metrics.percent_below_5 >= policy.critical_percent_below_5
        ):
            verdict = Verdict.VALIDATED_CRITICAL
        elif (
            metrics.minimum_k >= policy.minimum_k
            and metrics.percent_below_5 <= policy.maximum_percent_below_k5
        ):
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
    mitigation = None
    if spec.mitigation and spec.candidate:
        mitigation = simulate_mitigation(
            generate_rows(spec),
            spec.columns,
            drop=tuple(spec.mitigation.get("drop", ())),
            generalize=spec.mitigation.get("generalize", {}),
            action=str(spec.mitigation["action"]),
        )
    assessment = Assessment(
        candidate=candidate,
        verdict=verdict,
        reasons=reasons,
        metrics=metrics,
        aggregate_query=query,
        raw_rows_returned=0,
        mitigation=mitigation,
        adversarial_self_check=(
            "False-positive case considered: individually ordinary fields and high cardinality "
            "are not sufficient. The verdict is allowed only because independent upstream "
            "datasets converge and aggregate class counts breach the configured policy."
            if verdict is Verdict.VALIDATED_CRITICAL
            else None
        ),
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
        "policy": {
            "policy_id": policy.policy_id,
            "sha256": policy.sha256,
            "source": policy.source,
            "minimum_k": policy.minimum_k,
            "maximum_percent_below_k5": policy.maximum_percent_below_k5,
        },
        "exit_code": assessment.exit_code,
    }
