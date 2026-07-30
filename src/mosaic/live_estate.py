from __future__ import annotations

import time
from typing import Any


def seed_and_discover(server: str = "http://localhost:8080") -> dict[str, Any]:
    """Create a multi-asset synthetic estate, then discover its paths from Core."""
    from datahub.metadata.urns import DatasetUrn
    from datahub.sdk import DataHubClient, Dataset

    client = DataHubClient(server=server)
    client.test_connection()
    suffix = str(int(time.time()))
    source_a = Dataset(
        platform="duckdb",
        name=f"mosaic.contacts_{suffix}",
        schema=[("zip5", "string"), ("birth_date", "date")],
    )
    source_b = Dataset(
        platform="duckdb",
        name=f"mosaic.demographics_{suffix}",
        schema=[("gender_category", "string")],
    )
    export = Dataset(
        platform="duckdb",
        name=f"mosaic.research_export_{suffix}",
        schema=[("zip5", "string"), ("birth_date", "date"), ("gender_category", "string")],
    )
    consumers = [
        Dataset(
            platform="duckdb",
            name=f"mosaic.{name}_{suffix}",
            schema=[("zip5", "string"), ("birth_date", "date"), ("gender_category", "string")],
        )
        for name in ("partner_delivery", "cohort_explorer", "model_training")
    ]
    for asset in (source_a, source_b, export, *consumers):
        client.entities.upsert(asset)
    client.lineage.add_lineage(
        upstream=source_a.urn,
        downstream=export.urn,
        column_lineage={"zip5": ["zip5"], "birth_date": ["birth_date"]},
    )
    client.lineage.add_lineage(
        upstream=source_b.urn,
        downstream=export.urn,
        column_lineage={"gender_category": ["gender_category"]},
    )
    for consumer in consumers:
        client.lineage.add_lineage(
            upstream=export.urn,
            downstream=consumer.urn,
            column_lineage={field: [field] for field in ("zip5", "birth_date", "gender_category")},
        )
    urn = DatasetUrn(platform="duckdb", name=f"mosaic.research_export_{suffix}")
    upstream, downstream = [], []
    for _ in range(12):
        upstream = client.lineage.get_lineage(
            source_urn=urn, source_column="birth_date", direction="upstream", max_hops=1
        )
        downstream = client.lineage.get_lineage(source_urn=urn, direction="downstream", max_hops=1)
        if upstream and len(downstream) >= 3:
            break
        time.sleep(1)
    return {
        "status": "passed" if upstream and len(downstream) >= 3 else "failed",
        "export_urn": str(export.urn),
        "convergence": {
            "families": ["location", "date_of_birth", "demographic"],
            "upstream_paths": [str(x) for x in upstream],
        },
        "blast_radius": {
            "downstream_count": len(downstream),
            "assets": [str(x.urn) for x in downstream],
        },
        "codegen_context": {
            "asset": f"research_export_{suffix}",
            "asset_urn": str(export.urn),
            "columns": ["zip5", "birth_date", "gender_category"],
            "column_types": {
                "zip5": "varchar",
                "birth_date": "date",
                "gender_category": "varchar",
            },
            "families": ["location", "date_of_birth", "demographic"],
            "lineage_paths": [
                [str(source_a.urn), str(export.urn)],
                [str(source_b.urn), str(export.urn)],
            ],
            "downstream_assets": [str(x.urn) for x in downstream],
            "source_systems": [str(source_a.urn), str(source_b.urn)],
        },
        "synthetic_only": True,
    }
