from __future__ import annotations

from mosaic.query_policy import aggregate_query, validate_aggregate_query
from mosaic.scenario import build_synthetic_estate


def run_probe() -> dict[str, object]:
    """Execute the exact approved aggregate query in an isolated in-memory DuckDB."""
    import duckdb

    estate = build_synthetic_estate()
    columns = ("zip5", "birth_date", "gender_category")
    query = aggregate_query("research_export_clean", columns)
    validate_aggregate_query(query, "research_export_clean", columns)
    connection = duckdb.connect(":memory:")
    connection.execute(
        "CREATE TABLE research_export_clean (zip5 VARCHAR, birth_date VARCHAR, gender_category VARCHAR, diagnosis_group VARCHAR)"
    )
    connection.executemany(
        "INSERT INTO research_export_clean VALUES (?, ?, ?, ?)",
        [tuple(row.values()) for row in estate.rows],
    )
    groups = connection.execute(query).fetchall()
    sizes = [row[-1] for row in groups]
    return {
        "status": "passed",
        "query": query,
        "raw_rows_returned": 0,
        "metrics": {
            "total_records": sum(sizes),
            "distinct_combinations": len(groups),
            "minimum_k": min(sizes),
            "percent_below_5": round(100 * sum(s for s in sizes if s < 5) / sum(sizes), 3),
        },
    }
