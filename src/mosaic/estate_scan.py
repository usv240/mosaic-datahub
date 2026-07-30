from __future__ import annotations

from typing import Any

from mosaic.models import Verdict
from mosaic.scenario_registry import assess_scenario, list_scenarios

SEVERITY = {
    Verdict.VALIDATED_CRITICAL.value: 4,
    Verdict.VALIDATED_ELEVATED.value: 3,
    Verdict.SCREENING_ONLY.value: 2,
    Verdict.VALIDATED_LOW.value: 1,
    Verdict.INSUFFICIENT_METADATA.value: 0,
}


def scan_estate() -> dict[str, Any]:
    findings = []
    for spec in list_scenarios():
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
    return {
        "schema_version": 1,
        "status": "passed",
        "assets_screened": len(findings),
        "validated_findings": sum(item["verdict"].startswith("validated_") for item in findings),
        "critical_findings": sum(
            item["verdict"] == Verdict.VALIDATED_CRITICAL.value for item in findings
        ),
        "raw_rows_returned": sum(item["raw_rows_returned"] for item in findings),
        "ranked_findings": findings,
    }
