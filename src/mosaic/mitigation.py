from __future__ import annotations

from mosaic.models import RiskMetrics
from mosaic.risk import exact_k_metrics


def simulate_birth_date_suppression(rows: tuple[dict[str, str], ...]) -> dict[str, object]:
    """Shadow-only simulation: remove the most precise date field and recompute k."""
    metrics: RiskMetrics = exact_k_metrics(rows, ("zip5", "gender_category"))
    return {
        "status": "recommended" if metrics.minimum_k >= 5 else "insufficient",
        "action": "suppress birth_date from the research export",
        "evaluated_columns": ["zip5", "gender_category"],
        "metrics": {
            "minimum_k": metrics.minimum_k,
            "percent_below_5": metrics.percent_below_5,
            "distinct_combinations": metrics.distinct_combinations,
        },
        "writes_applied": False,
    }
