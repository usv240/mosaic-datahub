from __future__ import annotations

import json
import time
from typing import Any


def publish(server: str = "http://localhost:8080", *, approved: bool = False) -> dict[str, Any]:
    """Write all Mosaic evidence types and verify persistence by rereading each."""
    if not approved:
        return {"status": "awaiting_human_approval", "mutation_performed": False}

    from datahub.metadata.urns import TagUrn
    from datahub.sdk import DataHubClient, Dataset, Document, Tag

    from mosaic.datahub_graphql import (
        PROPERTY_URN,
        active_incidents,
        ensure_risk_property,
        raise_incident,
    )

    client = DataHubClient(server=server)
    client.test_connection()
    suffix = str(int(time.time()))
    target = Dataset(
        platform="duckdb",
        name=f"mosaic.governed_target_{suffix}",
        description="Synthetic target for Mosaic governed privacy evidence.",
        schema=[("zip5", "string"), ("birth_date", "date"), ("gender_category", "string")],
    )
    tag = Tag(
        name="mosaic:validated-critical",
        display_name="Mosaic validated critical",
        description="Approved compositional privacy-risk evidence on synthetic data.",
    )
    client.entities.upsert(tag)
    target.schema[0].add_tag(TagUrn("mosaic:validated-critical"))
    ensure_risk_property(server)
    target.set_structured_property(PROPERTY_URN, ["validated_critical"])
    client.entities.upsert(target)

    document = Document.create_document(
        id=f"mosaic-threat-model-{suffix}",
        title="Mosaic privacy threat model",
        text=(
            "# Mosaic synthetic threat model\n\nMinimum k: `1`  \n"
            "Records below k=5: `100%`  \nRaw person-level rows returned: `0`"
        ),
        subtype="Privacy Threat Model",
        related_assets=[str(target.urn)],
        custom_properties={"mosaic_risk_state": "validated_critical", "synthetic": "true"},
        show_in_global_context=False,
    )
    client.entities.upsert(document)
    incident_urn = raise_incident(server, str(target.urn), suffix, str(document.urn))

    reread = client.entities.get(target.urn)
    field = next(item for item in reread.schema if item.field_path == "zip5")
    reread_document = client.entities.get(document.urn)
    property_text = json.dumps(reread.structured_properties, default=str)
    incidents = active_incidents(server, str(target.urn))
    checks = {
        "field_tag_reread": str(TagUrn("mosaic:validated-critical"))
        in {str(item.tag) for item in field.tags},
        "structured_property_reread": PROPERTY_URN in property_text
        and "validated_critical" in property_text,
        "threat_document_reread": reread_document.title == document.title
        and str(target.urn) in (reread_document.related_assets or []),
        "active_incident_reread": any(
            item.get("urn") == incident_urn and item.get("status", {}).get("state") == "ACTIVE"
            for item in incidents
        ),
    }
    return {
        "status": "published" if all(checks.values()) else "verification_failed",
        "mutation_performed": True,
        "checks": checks,
        "entities": {
            "target": str(target.urn),
            "tag": str(tag.urn),
            "structured_property": PROPERTY_URN,
            "document": str(document.urn),
            "incident": incident_urn,
        },
    }
