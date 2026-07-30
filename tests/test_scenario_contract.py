from __future__ import annotations

from datetime import date

import pytest

from mosaic.query_policy import aggregate_query
from mosaic.scenario import HERO_URN, build_synthetic_estate


@pytest.mark.parametrize(
    "forbidden",
    ["name", "email", "ssn", "phone", "address", "member_id", "patient_id", "account_id"],
)
def test_fixture_contains_no_direct_identifier(forbidden: str) -> None:
    assert all(forbidden not in row for row in build_synthetic_estate().rows)


@pytest.mark.parametrize("required", ["zip5", "birth_date", "gender_category", "diagnosis_group"])
def test_fixture_rows_have_required_schema(required: str) -> None:
    estate = build_synthetic_estate()
    assert estate.rows
    assert all(required in row and row[required] for row in estate.rows)


@pytest.mark.parametrize(
    ("column", "expected_cardinality"),
    [("zip5", 6), ("gender_category", 3), ("diagnosis_group", 3)],
)
def test_fixture_domain_cardinality_is_stable(column: str, expected_cardinality: int) -> None:
    assert len({row[column] for row in build_synthetic_estate().rows}) == expected_cardinality


@pytest.mark.parametrize("column", ["zip5", "birth_date", "gender_category"])
def test_every_quasi_identifier_has_independent_lineage(column: str) -> None:
    estate = build_synthetic_estate()
    path = estate.lineage[column]
    assert len(path) == 2
    assert path[-1].startswith("research_export_clean.")
    assert path[0] != path[-1]


@pytest.mark.parametrize(
    "asset",
    ["research_partner_delivery", "cohort_explorer_export", "readmission_model_training"],
)
def test_blast_radius_contains_expected_consumers(asset: str) -> None:
    assert asset in build_synthetic_estate().downstream_assets


@pytest.mark.parametrize(
    ("asset", "columns", "expected"),
    [
        ("t", ("a",), "SELECT a, COUNT(*) AS equivalence_class_size FROM t GROUP BY a"),
        ("t", ("a", "b"), "SELECT a, b, COUNT(*) AS equivalence_class_size FROM t GROUP BY a, b"),
        (
            "safe_table",
            ("zip5",),
            "SELECT zip5, COUNT(*) AS equivalence_class_size FROM safe_table GROUP BY zip5",
        ),
        (
            "research_export_clean",
            ("zip5", "birth_date", "gender_category"),
            "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category",
        ),
    ],
)
def test_aggregate_query_generation_contract(asset, columns, expected) -> None:
    assert aggregate_query(asset, columns) == expected


def test_fixture_is_deterministic_and_has_expected_size() -> None:
    first = build_synthetic_estate()
    second = build_synthetic_estate()
    assert first == second
    assert len(first.rows) == 120


def test_all_fixture_dates_are_real_calendar_dates() -> None:
    for row in build_synthetic_estate().rows:
        assert date.fromisoformat(row["birth_date"]).isoformat() == row["birth_date"]


def test_hero_urn_is_a_production_dataset_urn() -> None:
    assert HERO_URN.startswith("urn:li:dataset:(urn:li:dataPlatform:mosaic,")
    assert HERO_URN.endswith(",PROD)")
