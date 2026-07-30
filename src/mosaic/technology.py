from __future__ import annotations

from typing import Any


def technology_catalog() -> dict[str, Any]:
    """Expose the sponsor technology map behind every Mosaic claim."""
    return {
        "schema_version": 1,
        "sponsor": {
            "name": "DataHub",
            "technology": "Open-source Context Platform",
            "role": "The context, action, and memory layer of the Mosaic agent.",
            "challenge": "Agents That Do Real Work + Open / Wildcard",
        },
        "workflow": [
            "Read schemas and fine-grained lineage",
            "Detect cross-source quasi-identifier convergence",
            "Trace downstream blast radius",
            "Validate with aggregate-only group counts",
            "Propose mitigation and publish reviewed context",
        ],
        "datahub_capabilities": [
            {
                "id": "context-graph",
                "surface": "Fine-grained lineage",
                "role": "Reconstructs which columns originate separately and converge in one asset.",
                "implementation": "src/mosaic/live_estate.py",
                "proof": "fixtures/datahub_recording/responses/lineage.json",
            },
            {
                "id": "blast-radius",
                "surface": "Downstream graph",
                "role": "Turns one validated finding into an estate-wide impact boundary.",
                "implementation": "src/mosaic/live_estate.py",
                "proof": "fixtures/datahub_recording/responses/downstream.json",
            },
            {
                "id": "sdk",
                "surface": "DataHub Python SDK",
                "role": "Creates synthetic assets and reads catalog entities through supported interfaces.",
                "implementation": "src/mosaic/live_estate.py",
                "proof": "fixtures/datahub_recording/responses/entity.json",
            },
            {
                "id": "graphql",
                "surface": "DataHub GraphQL API",
                "role": "Creates and verifies structured governance context and active incidents.",
                "implementation": "src/mosaic/datahub_graphql.py",
                "proof": "fixtures/datahub_recording/responses/writeback.json",
            },
            {
                "id": "mcp",
                "surface": "DataHub MCP Server",
                "role": "Makes schema, search, and lineage tools callable by an MCP-compatible agent.",
                "implementation": "src/mosaic/mcp_probe.py",
                "proof": "fixtures/datahub_recording/responses/mcp.json",
            },
            {
                "id": "skill",
                "surface": "DataHub Skills pattern",
                "role": "Packages the complete privacy workflow, judgment, safety, and failure handling.",
                "implementation": "skills/datahub-privacy-threat-model/SKILL.md",
                "proof": "skills/datahub-privacy-threat-model/evaluations/critical-convergence.json",
            },
            {
                "id": "writeback",
                "surface": "Tags, structured properties, Documents, and incidents",
                "role": "Leaves a reviewed decision in DataHub for the next human or agent.",
                "implementation": "src/mosaic/governed_writeback.py",
                "proof": "fixtures/datahub_recording/responses/writeback.json",
            },
        ],
        "differentiators": [
            {
                "label": "Graph-native privacy reasoning",
                "detail": "Finds risk created by relationships, beyond DataHub's out-of-box metadata views and beyond column scanners.",
            },
            {
                "label": "Aggregate-only proof",
                "detail": "A fail-closed SQL policy measures anonymity while keeping person-level rows at zero.",
            },
            {
                "label": "Reversible mitigation lab",
                "detail": "Compares privacy improvement and retained utility before proposing a catalog action.",
            },
            {
                "label": "Tamper-evident institutional memory",
                "detail": "Digest-backed evidence, re-read write-back, and retained decisions make the result inheritable.",
            },
        ],
        "supporting_stack": [
            {"name": "DuckDB", "role": "Isolated in-memory aggregate validation"},
            {"name": "FastAPI", "role": "Typed read-only demo and operator APIs"},
            {"name": "Playwright", "role": "End-to-end accessibility and judge-media verification"},
        ],
        "open_source_contribution": {
            "status": "merged",
            "project": "datahub-project/datahub",
            "pull_request": 18705,
            "url": "https://github.com/datahub-project/datahub/pull/18705",
        },
    }
