from __future__ import annotations

from collections import defaultdict
from typing import Any

from mosaic.compositional_join import AssetProfile, detect_cross_asset_risks
from mosaic.models import Verdict
from mosaic.scenario_registry import ScenarioSpec, assess_scenario, list_scenarios

SEVERITY = {
    Verdict.VALIDATED_CRITICAL.value: 4,
    Verdict.VALIDATED_ELEVATED.value: 3,
    Verdict.SCREENING_ONLY.value: 2,
    Verdict.VALIDATED_LOW.value: 1,
    Verdict.INSUFFICIENT_METADATA.value: 0,
}


def _source_profiles(specs: list[ScenarioSpec]) -> tuple[AssetProfile, ...]:
    """Build joinable upstream profiles only from explicit lineage and join-key metadata."""
    collected: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"join_keys": set(), "families": set()}
    )
    for spec in specs:
        for family, path in zip(spec.families, spec.lineage_paths, strict=True):
            source = path[0].split(".", 1)[0]
            urn = f"urn:li:dataset:(urn:li:dataPlatform:mosaic,{source},PROD)"
            collected[urn]["join_keys"].update(spec.join_keys)
            collected[urn]["families"].add(family)
    return tuple(
        AssetProfile(
            urn=urn,
            join_keys=tuple(sorted(profile["join_keys"])),
            families=tuple(sorted(profile["families"])),
        )
        for urn, profile in sorted(collected.items())
    )


def scan_estate() -> dict[str, Any]:
    specs = list_scenarios()
    findings = []
    for spec in specs:
        report = assess_scenario(spec.slug)
        assessment = report["assessment"]
        metrics = assessment["metrics"] or {}
        findings.append(
            {
                "scenario": spec.slug,
                "asset_urn": assessment["candidate"]["asset_urn"],
                "verdict": assessment["verdict"],
                "severity": SEVERITY[assessment["verdict"]],
                "minimum_k": metrics.get("minimum_k"),
                "percent_below_5": metrics.get("percent_below_5"),
                "lineage_delta": report["graph_value"]["delta"],
                "downstream_count": len(assessment["candidate"]["downstream_assets"]),
                "raw_rows_returned": assessment["raw_rows_returned"],
            }
        )
    findings.sort(
        key=lambda item: (
            -item["severity"],
            item["minimum_k"] if item["minimum_k"] is not None else 10**9,
            -item["downstream_count"],
            item["scenario"],
        )
    )
    cross_asset = [
        {
            "left_asset_urn": finding.left_urn,
            "right_asset_urn": finding.right_urn,
            "shared_join_keys": list(finding.shared_keys),
            "combined_families": list(finding.combined_families),
            "decision_reason": (
                "Each asset contributes distinct quasi-identifier context and DataHub metadata "
                "shows a shared join key; the combination requires aggregate validation."
            ),
            "status": "screening_candidate",
        }
        for finding in detect_cross_asset_risks(_source_profiles(specs))
    ]
    return {
        "schema_version": 2,
        "status": "passed",
        "assets_screened": len(findings),
        "validated_findings": sum(item["verdict"].startswith("validated_") for item in findings),
        "critical_findings": sum(
            item["verdict"] == Verdict.VALIDATED_CRITICAL.value for item in findings
        ),
        "cross_asset_candidates": len(cross_asset),
        "raw_rows_returned": sum(item["raw_rows_returned"] for item in findings),
        "ranked_findings": findings,
        "cross_asset_findings": cross_asset,
        "cross_asset_safety": {
            "verdict_scope": "metadata_screening_only",
            "raw_rows_returned": 0,
            "rule": "shared join key + distinct contributed families",
        },
    }
