from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from mosaic.models import RiskMetrics
from mosaic.risk import exact_k_metrics


def _generalize(value: str, rule: Any) -> str:
    if isinstance(rule, Mapping):
        if "mapping" in rule:
            return str(rule["mapping"].get(value, value))
        kind = rule.get("kind")
        if kind == "prefix":
            return value[: int(rule["length"])]
        if kind == "decade":
            return f"{int(value[:4]) // 10 * 10}s"
        if kind == "bucket":
            width = int(rule["width"])
            start = int(value) // width * width
            return f"{start}-{start + width - 1}"
    raise ValueError(f"unsupported generalization rule: {rule!r}")


def _utility_retained(
    before: tuple[dict[str, str], ...],
    after: tuple[dict[str, str], ...],
    columns: tuple[str, ...],
    retained: tuple[str, ...],
) -> float:
    scores = []
    for column in columns:
        if column not in retained:
            scores.append(0.0)
            continue
        before_cardinality = len({row[column] for row in before})
        after_cardinality = len({row[column] for row in after})
        if before_cardinality <= 1:
            scores.append(1.0)
        else:
            scores.append(math.log2(after_cardinality) / math.log2(before_cardinality))
    return round(sum(scores) / len(scores), 3)


def simulate_mitigation(
    rows: tuple[dict[str, str], ...],
    columns: tuple[str, ...],
    *,
    drop: tuple[str, ...] = (),
    generalize: Mapping[str, Any] | None = None,
    action: str = "apply configured privacy mitigation",
) -> dict[str, object]:
    """Apply a generic shadow transform and recompute privacy and utility from rows."""
    generalize = generalize or {}
    unknown = (set(drop) | set(generalize)) - set(columns)
    if unknown:
        raise ValueError(f"mitigation references unknown columns: {sorted(unknown)}")
    retained = tuple(column for column in columns if column not in drop)
    if not retained:
        raise ValueError("mitigation cannot suppress every assessment column")
    transformed = tuple(
        {
            column: _generalize(row[column], generalize[column])
            if column in generalize
            else row[column]
            for column in retained
        }
        for row in rows
    )
    metrics: RiskMetrics = exact_k_metrics(transformed, retained)
    return {
        "status": "recommended" if metrics.minimum_k >= 5 else "insufficient",
        "action": action,
        "drop": list(drop),
        "generalize": dict(generalize),
        "evaluated_columns": list(retained),
        "metrics": {
            "minimum_k": metrics.minimum_k,
            "percent_below_5": metrics.percent_below_5,
            "distinct_combinations": metrics.distinct_combinations,
        },
        "utility_retained": _utility_retained(rows, transformed, columns, retained),
        "writes_applied": False,
    }


def simulate_birth_date_suppression(rows: tuple[dict[str, str], ...]) -> dict[str, object]:
    return simulate_mitigation(
        rows,
        ("zip5", "birth_date", "gender_category"),
        drop=("birth_date",),
        action="suppress birth_date from the research export",
    )
