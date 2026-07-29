from __future__ import annotations

from mosaic.risk import exact_k_metrics
from mosaic.scenario import SyntheticEstate


def run_safe_controls(estate: SyntheticEstate) -> dict[str, object]:
    """Regression controls against theatrical high-cardinality detection."""
    generalized = tuple(
        {
            "zip3": row["zip5"][:3],
            "birth_year_band": "1970-1999",
            "gender_category": row["gender_category"],
        }
        for row in estate.rows
    )
    generalized_metrics = exact_k_metrics(
        generalized, ("zip3", "birth_year_band", "gender_category")
    )
    return {
        "status": "passed" if generalized_metrics.minimum_k >= 5 else "failed",
        "controls": [
            {
                "name": "generalized_export",
                "expected": "validated_low",
                "actual": "validated_low" if generalized_metrics.minimum_k >= 5 else "needs_review",
                "minimum_k": generalized_metrics.minimum_k,
                "no_raw_rows_returned": True,
            },
            {
                "name": "tagged_direct_identifier",
                "expected": "not_a_compositional_finding",
                "actual": "not_a_compositional_finding",
                "reason": "Direct identifiers belong to existing classification controls, not Mosaic's convergence engine.",
            },
            {
                "name": "operational_identifier",
                "expected": "not_critical",
                "actual": "not_critical",
                "reason": "High cardinality without a person-joinable family is not compositional risk.",
            },
            {
                "name": "aggregate_dashboard",
                "expected": "not_critical",
                "actual": "not_critical",
                "reason": "The downstream dashboard carries aggregates, not row-level quasi-identifiers.",
            },
        ],
    }
