from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any


async def run_probe(
    mcp_url: str = "http://127.0.0.1:8000/mcp",
    datahub_server: str = "http://localhost:8080",
) -> dict[str, Any]:
    """Prove Mosaic discovery, lineage, and governed tagging through official MCP."""
    from datahub.sdk import DataHubClient, Dataset, Tag
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    client = DataHubClient(server=datahub_server)
    suffix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    source = Dataset(
        platform="duckdb", name=f"mosaic.mcp_contacts_{suffix}", schema=[("birth_date", "date")]
    )
    target = Dataset(
        platform="duckdb", name=f"mosaic.mcp_export_{suffix}", schema=[("birth_date", "date")]
    )
    tag = Tag(
        name="mosaic:mcp-verified",
        display_name="Mosaic MCP verified",
        description="Synthetic governed MCP proof.",
    )
    for entity in (source, target, tag):
        client.entities.upsert(entity)
    client.lineage.add_lineage(
        upstream=source.urn, downstream=target.urn, column_lineage={"birth_date": ["birth_date"]}
    )

    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            tool_names = {tool.name for tool in listed.tools}
            search_results = []
            for _ in range(10):
                search = await session.call_tool(
                    "search", {"query": f"mosaic.mcp_export_{suffix}", "num_results": 10}
                )
                search_results = (search.structuredContent or {}).get("searchResults", [])
                if search_results:
                    break
                await asyncio.sleep(1)
            if not search_results:
                raise RuntimeError("MCP search did not find the seeded Mosaic export")
            target_urn = search_results[0]["entity"]["urn"]
            lineage = await session.call_tool(
                "get_lineage",
                {"urn": target_urn, "column": "birth_date", "upstream": True, "max_hops": 1},
            )
            mutation = await session.call_tool(
                "add_tags",
                {
                    "tag_urns": [str(tag.urn)],
                    "entity_urns": [target_urn],
                    "column_paths": ["birth_date"],
                },
            )
            reread = await session.call_tool("get_entities", {"urns": [target_urn]})

    checks = {
        "required_tools_exposed": {"search", "get_entities", "get_lineage", "add_tags"}
        <= tool_names,
        "search_found_seeded_asset": bool(search_results),
        "column_lineage_read_through_mcp": not lineage.isError
        and "birth_date" in json.dumps(lineage.structuredContent or {}),
        "field_tag_mutation_and_reread_through_mcp": not mutation.isError
        and "Mosaic MCP verified" in json.dumps(reread.structuredContent or {}),
    }
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "server": {"name": initialized.serverInfo.name, "version": initialized.serverInfo.version},
        "target_urn": target_urn,
        "available_tools": sorted(tool_names),
    }


def run() -> dict[str, Any]:
    return asyncio.run(run_probe())
