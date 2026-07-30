from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given
from hypothesis import strategies as st

from mosaic.discovery import discover_convergences, graph_value_report
from mosaic.models import Assessment, Candidate, RiskMetrics, Verdict
from mosaic.query_policy import QueryPolicyError, aggregate_query, validate_aggregate_query
from mosaic.risk import exact_k_metrics
from mosaic.scenario import HERO_URN, SyntheticEstate, build_synthetic_estate


def _rows(class_sizes: tuple[int, ...]) -> tuple[dict[str, str], ...]:
    return tuple(
        {"key": f"class-{index}"} for index, size in enumerate(class_sizes) for _ in range(size)
    )


@pytest.mark.parametrize(
    ("sizes", "minimum_k", "below_2", "below_5", "below_10"),
    [
        ((1,), 1, 100.0, 100.0, 100.0),
        ((2,), 2, 0.0, 100.0, 100.0),
        ((5,), 5, 0.0, 0.0, 100.0),
        ((10,), 10, 0.0, 0.0, 0.0),
        ((1, 1), 1, 100.0, 100.0, 100.0),
        ((1, 2), 1, 33.333, 100.0, 100.0),
        ((1, 4), 1, 20.0, 100.0, 100.0),
        ((1, 5), 1, 16.667, 16.667, 100.0),
        ((1, 10), 1, 9.091, 9.091, 9.091),
        ((2, 3), 2, 0.0, 100.0, 100.0),
        ((4, 5), 4, 0.0, 44.444, 100.0),
        ((5, 5), 5, 0.0, 0.0, 100.0),
        ((9, 10), 9, 0.0, 0.0, 47.368),
        ((10, 10), 10, 0.0, 0.0, 0.0),
        ((1, 2, 5, 10), 1, 5.556, 16.667, 44.444),
    ],
)
def test_exact_k_boundary_matrix(sizes, minimum_k, below_2, below_5, below_10) -> None:
    metrics = exact_k_metrics(_rows(sizes), ("key",))
    assert metrics.total_records == sum(sizes)
    assert metrics.distinct_combinations == len(sizes)
    assert metrics.minimum_k == minimum_k
    assert metrics.percent_below_2 == below_2
    assert metrics.percent_below_5 == below_5
    assert metrics.percent_below_10 == below_10


@given(st.lists(st.integers(min_value=1, max_value=25), min_size=1, max_size=20))
def test_exact_k_property_invariants(sizes: list[int]) -> None:
    metrics = exact_k_metrics(_rows(tuple(sizes)), ("key",))
    assert metrics.total_records == sum(sizes)
    assert metrics.distinct_combinations == len(sizes)
    assert metrics.minimum_k == min(sizes)
    assert (
        0 <= metrics.percent_below_2 <= metrics.percent_below_5 <= metrics.percent_below_10 <= 100
    )
    assert sum(size * count for size, count in metrics.class_size_distribution.items()) == sum(
        sizes
    )


def test_exact_k_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="empty asset"):
        exact_k_metrics((), ("key",))


def test_exact_k_fails_closed_on_missing_column() -> None:
    with pytest.raises(KeyError):
        exact_k_metrics(({"other": "value"},), ("key",))


SAFE_COLUMNS = ("zip5", "birth_date", "gender_category")


@pytest.mark.parametrize(
    "query",
    [
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category;",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean WHERE 1=1 GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean HAVING COUNT(*) > 1 GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category ORDER BY zip5",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category LIMIT 10",
        "SELECT * FROM research_export_clean",
        "SELECT zip5 FROM research_export_clean",
        "DELETE FROM research_export_clean",
        "UPDATE research_export_clean SET zip5='x'",
        "INSERT INTO research_export_clean VALUES ('x')",
        "SELECT zip5, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5 UNION SELECT zip5, 1 FROM other",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM other GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, diagnosis_group, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, diagnosis_group",
        "SELECT birth_date, zip5, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY birth_date, zip5, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(zip5) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS n FROM research_export_clean GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, MIN(zip5), COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, birth_date, gender_category, diagnosis_group",
        "SELECT zip5, zip5, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5, zip5, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean JOIN other ON true GROUP BY zip5, birth_date, gender_category",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean -- comment\n GROUP BY zip5, birth_date, gender_category",
        "",
        "research_export_clean",
    ],
)
def test_query_policy_adversarial_matrix(query: str) -> None:
    with pytest.raises(QueryPolicyError):
        validate_aggregate_query(query, "research_export_clean", SAFE_COLUMNS)


@pytest.mark.parametrize(
    "query",
    [
        aggregate_query("research_export_clean", SAFE_COLUMNS),
        "  SELECT   zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size   FROM research_export_clean GROUP BY zip5, birth_date, gender_category  ",
        "select zip5, birth_date, gender_category, count(*) as equivalence_class_size from research_export_clean group by zip5, birth_date, gender_category",
    ],
)
def test_query_policy_accepts_only_equivalent_whitespace_and_case(query: str) -> None:
    validate_aggregate_query(query, "research_export_clean", SAFE_COLUMNS)


@pytest.mark.parametrize("verdict", list(Verdict))
def test_assessment_exit_code_contract(verdict: Verdict) -> None:
    candidate = Candidate("urn:test", ("x",), ("location",), (("a", "b"),), True, ())
    assessment = Assessment(candidate, verdict, (), None, None, 0)
    assert assessment.exit_code == (3 if verdict is Verdict.VALIDATED_CRITICAL else 0)
    assert assessment.to_dict()["verdict"] == verdict.value


@pytest.mark.parametrize("model", [Candidate, RiskMetrics, Assessment])
def test_domain_models_are_frozen(model) -> None:
    candidate = Candidate("urn:test", ("x",), ("location",), (("a",),), True, ())
    values = {
        Candidate: candidate,
        RiskMetrics: RiskMetrics(1, 1, 1, 100.0, 100.0, 100.0, {1: 1}),
        Assessment: Assessment(candidate, Verdict.SCREENING_ONLY, (), None, None, 0),
    }
    with pytest.raises(FrozenInstanceError):
        values[model].asset_urn = "changed"  # type: ignore[attr-defined]


def test_discovery_requires_multiple_columns_and_families() -> None:
    one_column = SyntheticEstate(({"zip5": "1"},), {"zip5": "location"}, {"zip5": ("a",)}, ())
    same_family = SyntheticEstate(
        ({"zip5": "1", "zip3": "1"},),
        {"zip5": "location", "zip3": "location"},
        {"zip5": ("a",), "zip3": ("b",)},
        (),
    )
    assert discover_convergences(one_column) == []
    assert discover_convergences(same_family) == []


def test_discovery_preserves_graph_evidence() -> None:
    estate = build_synthetic_estate()
    candidate = discover_convergences(estate)[0]
    assert candidate.asset_urn == HERO_URN
    assert candidate.columns == tuple(estate.column_families)
    assert candidate.lineage_paths == tuple(estate.lineage[column] for column in candidate.columns)
    assert candidate.downstream_assets == estate.downstream_assets
    assert graph_value_report(estate)["status"] == "passed"
