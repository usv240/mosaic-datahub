from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from typing import Any

ADULT_COLUMNS = (
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education_num",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "native_country",
    "income",
)


def parse_adult(data: bytes) -> list[dict[str, str]]:
    """Parse Adult records in memory; callers need never persist source rows."""
    text = data.decode("utf-8")
    records: list[dict[str, str]] = []
    for values in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not values or len(values) != len(ADULT_COLUMNS):
            continue
        records.append(dict(zip(ADULT_COLUMNS, (value.strip() for value in values), strict=True)))
    if not records:
        raise ValueError("Adult source contained no valid records")
    return records


def _generalized(record: dict[str, str]) -> dict[str, str]:
    age = int(record["age"])
    return {
        "age_band": f"{age // 10 * 10}s",
        "education": record["education"],
        "marital_status": record["marital_status"],
        "occupation": record["occupation"],
        "sex": record["sex"],
        "native_country": record["native_country"],
    }


def _aggregate(rows: list[dict[str, str]], columns: tuple[str, ...]) -> dict[str, Any]:
    classes = Counter(tuple(row[column] for column in columns) for row in rows)
    total = len(rows)
    below_five = sum(size for size in classes.values() if size < 5)
    return {
        "columns": list(columns),
        "records": total,
        "distinct_combinations": len(classes),
        "minimum_k": min(classes.values()),
        "percent_below_5": round(100 * below_five / total, 3),
        "raw_rows_returned": 0,
    }


def build_adult_proof(data: bytes) -> dict[str, Any]:
    records = parse_adult(data)
    generalized = [_generalized(record) for record in records]
    single = _aggregate(generalized, ("age_band",))
    composed = _aggregate(
        generalized,
        ("age_band", "education", "marital_status", "occupation", "sex", "native_country"),
    )
    return {
        "schema_version": 1,
        "status": "passed" if composed["minimum_k"] < single["minimum_k"] else "failed",
        "source": {
            "name": "UCI Adult",
            "official_page": "https://archive.ics.uci.edu/dataset/2/adult",
            "doi": "10.24432/C5XW20",
            "license": "CC BY 4.0",
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "records_processed_in_memory": len(records),
            "raw_rows_committed": 0,
        },
        "method": {
            "purpose": "Demonstrate how individually ordinary attributes can produce small equivalence classes when composed.",
            "generalization": "Age is grouped by decade; categorical values otherwise retain the source labels.",
            "missing_values": "Question-mark source categories are retained as explicit unknown values.",
            "limitations": "This 1994 census-derived dataset is a reproducible mechanism check, not a claim about current populations or production risk prevalence.",
        },
        "single_attribute_control": single,
        "composed_attributes": composed,
        "privacy": {
            "committed_artifact_contains": "Aggregate counts, hashes, provenance, and methodology only.",
            "committed_artifact_excludes": "Every person-level source row and every equivalence-class value.",
        },
    }
