"""Measure compositional re-identification risk in a file the operator supplies.

Everything else in Mosaic runs on committed fixtures, which answers "does the
mechanism work" but not "would it find anything in mine". This command closes
that gap: point it at a CSV and it applies the same aggregate-only rule the
scenarios use.

The output is deliberately value-free. Equivalence-class values *are* the
identifying combination, so echoing them back would leak exactly what the tool
exists to protect. Only counts, distributions, and column names leave this
module.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from pathlib import Path
from typing import Any

from mosaic.models import RiskMetrics
from mosaic.policy import PrivacyPolicy, load_policy
from mosaic.query_policy import aggregate_query, validate_aggregate_query

MAX_PREVIEW_CLASS_SIZES = 12


def parse_delimited(data: bytes, delimiter: str = ",") -> tuple[list[dict[str, str]], list[str]]:
    """Parse a delimited file in memory; callers never persist the rows."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("input must be UTF-8 encoded text") from error
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("input has no header row")
    header = [name.strip() for name in reader.fieldnames if name and name.strip()]
    if not header:
        raise ValueError("input has no usable column names")
    rows = [row for row in reader if any((value or "").strip() for value in row.values())]
    if not rows:
        raise ValueError("input has a header but no data rows")
    return rows, header


def _metrics(rows: list[dict[str, str]], columns: tuple[str, ...]) -> RiskMetrics:
    classes = Counter(tuple((row.get(column) or "").strip() for column in columns) for row in rows)
    total = sum(classes.values())

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


def _verdict(metrics: RiskMetrics, policy: PrivacyPolicy) -> tuple[str, str]:
    if (
        metrics.minimum_k < policy.critical_minimum_k
        and metrics.percent_below_5 >= policy.critical_percent_below_5
    ):
        return "validated_critical", (
            f"Smallest group is {metrics.minimum_k} and "
            f"{metrics.percent_below_5:.3f}% of records fall below k=5."
        )
    if (
        metrics.minimum_k >= policy.minimum_k
        and metrics.percent_below_5 <= policy.maximum_percent_below_k5
    ):
        return "validated_low", (
            f"Smallest group is {metrics.minimum_k}, at or above the configured "
            f"minimum of {policy.minimum_k}."
        )
    return "validated_elevated", (
        f"Smallest group is {metrics.minimum_k}, below the configured minimum of "
        f"{policy.minimum_k} but not past the critical rule."
    )


def measure_columns(
    data: bytes,
    columns: tuple[str, ...],
    *,
    asset: str = "operator_supplied_table",
    delimiter: str = ",",
    policy: PrivacyPolicy | None = None,
    source_name: str = "operator-supplied file",
) -> dict[str, Any]:
    """Measure anonymity for a caller's own columns under the standard query policy."""
    if len(columns) < 2:
        raise ValueError("measure at least two columns; one column is not a combination")
    if len(set(columns)) != len(columns):
        raise ValueError("columns must be distinct")
    rows, header = parse_delimited(data, delimiter)
    missing = [column for column in columns if column not in header]
    if missing:
        raise ValueError(
            "columns not found in the header: "
            + ", ".join(missing)
            + ". Available: "
            + ", ".join(header)
        )
    query = aggregate_query(asset, columns)
    validate_aggregate_query(query, asset, columns)
    active = policy or load_policy()
    metrics = _metrics(rows, columns)
    verdict, reason = _verdict(metrics, active)
    distribution = dict(list(metrics.class_size_distribution.items())[:MAX_PREVIEW_CLASS_SIZES])
    return {
        "schema_version": 1,
        "status": verdict,
        "source": {
            "name": source_name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "columns_measured": list(columns),
            "columns_available": len(header),
            "records_processed_in_memory": metrics.total_records,
        },
        "aggregate_query": query,
        "metrics": {
            "total_records": metrics.total_records,
            "distinct_combinations": metrics.distinct_combinations,
            "minimum_k": metrics.minimum_k,
            "percent_below_2": metrics.percent_below_2,
            "percent_below_5": metrics.percent_below_5,
            "percent_below_10": metrics.percent_below_10,
            "class_size_distribution": distribution,
        },
        "reason": reason,
        "policy": {
            "policy_id": active.policy_id,
            "sha256": active.sha256,
            "source": active.source,
            "minimum_k": active.minimum_k,
            "maximum_percent_below_k5": active.maximum_percent_below_k5,
        },
        "privacy": {
            "raw_person_rows_returned": 0,
            "committed_output_contains": "Counts, distributions, column names, and a source digest.",
            "committed_output_excludes": (
                "Every source row and every equivalence-class value, because the "
                "combination itself is the identifier."
            ),
        },
        "limitations": (
            "This is an anonymity measurement of the columns you named, not a privacy "
            "review. It does not discover which columns are quasi-identifiers; use "
            "`mosaic discover` against DataHub for that. Thresholds are organization "
            "policy, not a legal conclusion."
        ),
    }


def measure_file(
    path: Path,
    columns: tuple[str, ...],
    *,
    delimiter: str = ",",
    policy: PrivacyPolicy | None = None,
) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    return measure_columns(
        data,
        columns,
        delimiter=delimiter,
        policy=policy,
        source_name=path.name,
    )
