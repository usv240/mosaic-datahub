import pytest

from mosaic.query_policy import QueryPolicyError, aggregate_query, validate_aggregate_query


def test_permits_the_exact_allowlisted_aggregate() -> None:
    columns = ("zip5", "birth_date", "gender_category")
    query = aggregate_query("research_export_clean", columns)
    validate_aggregate_query(query, "research_export_clean", columns)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT zip5, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY zip5; DELETE FROM x",
        "SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size FROM research_export_clean JOIN support_contacts ON 1=1 GROUP BY zip5, birth_date, gender_category",
        "SELECT diagnosis_group, COUNT(*) AS equivalence_class_size FROM research_export_clean GROUP BY diagnosis_group",
    ],
)
def test_rejects_non_aggregate_or_unapproved_queries(query: str) -> None:
    with pytest.raises(QueryPolicyError):
        validate_aggregate_query(
            query,
            "research_export_clean",
            ("zip5", "birth_date", "gender_category"),
        )
