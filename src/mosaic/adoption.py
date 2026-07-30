from __future__ import annotations

from typing import Any


def adoption_catalog() -> dict[str, Any]:
    """Describe honest paths from public evaluation to a governed deployment."""
    return {
        "schema_version": 1,
        "status": "ready_to_evaluate",
        "promise": (
            "Find compositional privacy risk, prove it with aggregate counts, and leave a "
            "reviewable decision in DataHub."
        ),
        "audiences": [
            {
                "id": "privacy",
                "label": "Privacy teams",
                "outcome": "Catch re-identification risk before a release is approved.",
            },
            {
                "id": "data",
                "label": "Data teams",
                "outcome": "See the exact lineage paths and mitigation trade-offs behind a finding.",
            },
            {
                "id": "governance",
                "label": "Governance teams",
                "outcome": "Keep evidence, ownership, incidents, and review state in the catalog.",
            },
            {
                "id": "security",
                "label": "Security teams",
                "outcome": "Prioritize exposure by validated anonymity and downstream reach.",
            },
        ],
        "paths": [
            {
                "id": "explore",
                "label": "Explore",
                "readiness": "available_now",
                "setup": "No credentials",
                "action": "Run four guided cases in the read-only hosted demo.",
                "proof": "Understand the risk, safety boundary, evidence, and mitigations.",
            },
            {
                "id": "evaluate",
                "label": "Evaluate",
                "readiness": "available_now",
                "setup": "Python 3.11+",
                "action": "Run the CLI, benchmark, fixture replay, and packaged agent skill.",
                "proof": "Reproduce engine behavior and integration semantics offline.",
            },
            {
                "id": "connect",
                "label": "Connect DataHub",
                "readiness": "configuration_required",
                "setup": "Disposable DataHub Core",
                "action": "Run live discovery and dry-run governance against synthetic assets.",
                "proof": "Verify SDK, GraphQL, MCP, lineage, blast radius, and re-read behavior.",
            },
            {
                "id": "operate",
                "label": "Operate",
                "readiness": "production_hardening_required",
                "setup": "Organization controls",
                "action": "Add SSO, approved query adapters, asset allowlists, and policy owners.",
                "proof": "Move from technical evidence to an accountable operating process.",
            },
        ],
        "connectors": [
            {
                "id": "datahub",
                "label": "DataHub Core",
                "status": "implemented",
                "detail": "SDK, GraphQL, MCP, lineage, downstream impact, and governed write-back.",
            },
            {
                "id": "duckdb",
                "label": "DuckDB",
                "status": "implemented",
                "detail": "In-memory aggregate validation for the reproducible reference workflow.",
            },
            {
                "id": "warehouse",
                "label": "Snowflake warehouse",
                "status": "adapter_implemented_credentials_required",
                "detail": "Optional DB-API adapter executes aggregate queries; deployment supplies credentials and query identity.",
            },
            {
                "id": "identity",
                "label": "SSO and RBAC",
                "status": "integration_required",
                "detail": "Required at the deployment boundary; the public demo remains read-only.",
            },
        ],
        "production_gates": [
            "Approved assets and query identities",
            "Organization-owned anonymity thresholds",
            "SSO, RBAC, audit retention, and secret management",
            "Warehouse-specific aggregate adapter validation",
            "Named human reviewers for catalog publication",
        ],
    }
