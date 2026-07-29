from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from mosaic.models import RiskMetrics


def exact_k_metrics(rows: Iterable[dict[str, str]], columns: tuple[str, ...]) -> RiskMetrics:
    """Equivalent to the approved GROUP BY query; consumes fixture rows internally only."""
    classes = Counter(tuple(row[column] for column in columns) for row in rows)
    total = sum(classes.values())
    if not total:
        raise ValueError("cannot assess an empty asset")

    def percentage(limit: int) -> float:
        return round(100 * sum(size for size in classes.values() if size < limit) / total, 3)

    return RiskMetrics(
        total_records=total,
        distinct_combinations=len(classes),
        minimum_k=min(classes.values()),
        percent_below_2=percentage(2),
        percent_below_5=percentage(5),
        percent_below_10=percentage(10),
        class_size_distribution=dict(sorted(Counter(classes.values()).items())),
    )
