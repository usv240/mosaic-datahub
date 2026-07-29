from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import Request, urlopen

PROPERTY_URN = "urn:li:structuredProperty:mosaic.riskState"


def graphql(server: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        server.rstrip("/") + "/api/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read())
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    return payload.get("data") or {}


def ensure_risk_property(server: str) -> None:
    if property_ready(server):
        return
    graphql(
        server,
        """mutation Create($input: CreateStructuredPropertyInput!) {
          createStructuredProperty(input: $input) { urn }
        }""",
        {
            "input": {
                "id": "mosaic.riskState",
                "qualifiedName": "mosaic.riskState",
                "displayName": "Mosaic privacy risk state",
                "description": "Aggregate-validated compositional privacy-risk state.",
                "valueType": "urn:li:dataType:datahub.string",
                "cardinality": "SINGLE",
                "entityTypes": ["urn:li:entityType:datahub.dataset"],
            }
        },
    )
    for _ in range(10):
        if property_ready(server):
            return
        time.sleep(1)
    raise RuntimeError("Mosaic structured property was not readable after creation")


def property_ready(server: str) -> bool:
    data = graphql(
        server,
        "query P($urn: String!) { structuredProperty(urn: $urn) { definition { qualifiedName } } }",
        {"urn": PROPERTY_URN},
    )
    definition = (data.get("structuredProperty") or {}).get("definition") or {}
    return definition.get("qualifiedName") == "mosaic.riskState"


def raise_incident(server: str, target_urn: str, suffix: str, document_urn: str) -> str:
    data = graphql(
        server,
        "mutation R($input: RaiseIncidentInput!) { raiseIncident(input: $input) }",
        {
            "input": {
                "resourceUrn": target_urn,
                "type": "CUSTOM",
                "customType": "PRIVACY_RISK",
                "title": f"Mosaic privacy review required: {suffix}",
                "description": f"Synthetic aggregate-only evidence: {document_urn}",
            }
        },
    )
    urn = data.get("raiseIncident")
    if not isinstance(urn, str):
        raise RuntimeError("DataHub did not return an incident URN")
    return urn


def active_incidents(server: str, target_urn: str) -> list[dict[str, Any]]:
    for _ in range(10):
        data = graphql(
            server,
            """query I($urn: String!) { dataset(urn: $urn) {
              incidents(state: ACTIVE, start: 0, count: 20) {
                incidents { urn title status { state } }
              }
            } }""",
            {"urn": target_urn},
        )
        items = ((data.get("dataset") or {}).get("incidents") or {}).get("incidents") or []
        if items:
            return items
        time.sleep(1)
    return []
