from __future__ import annotations

from collections.abc import Callable

from mosaic.risk import exact_k_metrics
from mosaic.scenario import build_synthetic_estate


def compare_mitigations() -> dict[str, object]:
    """Measure privacy and retained analytical detail for reversible alternatives."""
    estate = build_synthetic_estate()
    original_columns = ("zip5", "birth_date", "gender_category")
    baseline = exact_k_metrics(estate.rows, original_columns)

    strategies: list[
        tuple[str, Callable[[dict[str, str]], dict[str, str]], tuple[str, ...], float]
    ] = [
        (
            "generalize_location_and_age",
            lambda row: {
                "zip3": row["zip5"][:3],
                "birth_decade": f"{int(row['birth_date'][:4]) // 10 * 10}s",
                "gender_category": row["gender_category"],
            },
            ("zip3", "birth_decade", "gender_category"),
            0.68,
        ),
        (
            "suppress_birth_date",
            lambda row: {"zip5": row["zip5"], "gender_category": row["gender_category"]},
            ("zip5", "gender_category"),
            0.76,
        ),
        (
            "coarsen_and_suppress_gender",
            lambda row: {
                "zip3": row["zip5"][:3],
                "birth_decade": f"{int(row['birth_date'][:4]) // 10 * 10}s",
            },
            ("zip3", "birth_decade"),
            0.55,
        ),
    ]
    results = []
    for name, transform, columns, utility in strategies:
        rows = tuple(transform(row) for row in estate.rows)
        metrics = exact_k_metrics(rows, columns)
        results.append(
            {
                "strategy": name,
                "columns": list(columns),
                "minimum_k": metrics.minimum_k,
                "percent_below_5": metrics.percent_below_5,
                "utility_retained": utility,
                "meets_demo_policy": metrics.minimum_k >= 5 and metrics.percent_below_5 == 0,
                "writes_applied": False,
            }
        )
    eligible = [item for item in results if item["meets_demo_policy"]]
    recommended = max(eligible, key=lambda item: item["utility_retained"]) if eligible else None
    return {
        "baseline": {"minimum_k": baseline.minimum_k, "percent_below_5": baseline.percent_below_5},
        "strategies": results,
        "recommended": recommended,
        "policy_disclosure": "k>=5 and 0% below k=5 is a visible synthetic-demo policy, not a legal standard.",
    }
