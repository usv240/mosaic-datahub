from __future__ import annotations

from mosaic.controls import run_safe_controls
from mosaic.discovery import discover_convergences, graph_value_report
from mosaic.mitigation import simulate_birth_date_suppression
from mosaic.models import Assessment, Verdict
from mosaic.query_policy import aggregate_query, validate_aggregate_query
from mosaic.risk import exact_k_metrics
from mosaic.scenario import HERO_URN, build_synthetic_estate
from mosaic.writeback import build_proposal


def assess_demo() -> Assessment:
    estate = build_synthetic_estate()
    candidates = discover_convergences(estate)
    if not candidates:
        raise RuntimeError("fixture did not expose a lineage convergence")
    candidate = candidates[0]
    query = aggregate_query("research_export_clean", candidate.columns)
    validate_aggregate_query(query, "research_export_clean", candidate.columns)
    metrics = exact_k_metrics(estate.rows, candidate.columns)
    critical = metrics.minimum_k < 2 and metrics.percent_below_5 >= 20
    verdict = Verdict.VALIDATED_CRITICAL if critical else Verdict.VALIDATED_ELEVATED
    reasons = (
        "Three quasi-identifier families converge through independent lineage paths.",
        f"Exact aggregate validation found minimum k={metrics.minimum_k} and "
        f"{metrics.percent_below_5:.3f}% of records in classes below k=5.",
        f"The combination reaches {len(candidate.downstream_assets)} downstream assets.",
    )
    return Assessment(
        candidate=candidate,
        verdict=verdict,
        reasons=reasons,
        metrics=metrics,
        aggregate_query=query,
        raw_rows_returned=0,
        mitigation=simulate_birth_date_suppression(estate.rows),
        adversarial_self_check=(
            "False-positive case considered: the fields are not direct identifiers and each "
            "source alone is ordinary. Independent lineage convergence plus measured k=1 "
            "is the evidence that defeats that alternative explanation."
        ),
    )


def run_judge_demo() -> dict[str, object]:
    full_assessment = assess_demo()
    assessment = full_assessment.to_dict()
    report = {
        "product": "Mosaic",
        "synthetic_data_only": True,
        "assessment": assessment,
        "graph_value": graph_value_report(build_synthetic_estate()),
        "safe_controls": run_safe_controls(build_synthetic_estate()),
        "writeback": {
            "status": "dry_run",
            "requires_reviewer_approval": True,
            "target_urn": HERO_URN,
            "proposal": build_proposal(full_assessment),
        },
        "exit_code": assessment["exit_code"],
    }
    return report
