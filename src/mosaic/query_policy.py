from __future__ import annotations

import re


class QueryPolicyError(ValueError):
    pass


def aggregate_query(asset: str, columns: tuple[str, ...]) -> str:
    identifiers = ", ".join(columns)
    return f"SELECT {identifiers}, COUNT(*) AS equivalence_class_size FROM {asset} GROUP BY {identifiers}"


def validate_aggregate_query(
    query: str, allowed_asset: str, allowed_columns: tuple[str, ...]
) -> None:
    """Fail closed: one approved table, grouping keys, and COUNT(*) only."""
    compact = " ".join(query.strip().split())
    if ";" in compact or re.search(
        r"\b(JOIN|WHERE|HAVING|ORDER|LIMIT|UNION|INSERT|UPDATE|DELETE)\b", compact, re.I
    ):
        raise QueryPolicyError("only a single aggregate GROUP BY query is permitted")
    escaped_asset = re.escape(allowed_asset)
    match = re.fullmatch(
        rf"SELECT (.+), COUNT\(\*\) AS equivalence_class_size FROM {escaped_asset} GROUP BY (.+)",
        compact,
        re.I,
    )
    if not match:
        raise QueryPolicyError("query does not match the approved aggregate shape")
    selected = tuple(part.strip() for part in match.group(1).split(","))
    grouped = tuple(part.strip() for part in match.group(2).split(","))
    if selected != allowed_columns or grouped != allowed_columns:
        raise QueryPolicyError("only the approved quasi-identifier columns may be grouped")
