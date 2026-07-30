from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

import mosaic.governed_writeback as governed
import mosaic.live_estate as live
import mosaic.mcp_probe as mcp_probe


def _module(name: str, **attributes) -> ModuleType:
    module = ModuleType(name)
    module.__dict__.update(attributes)
    module.__path__ = []  # type: ignore[attr-defined]
    return module


def _install(monkeypatch, modules: dict[str, ModuleType]) -> None:
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)


class _Urn(str):
    @property
    def urn(self):
        return self


class _Dataset:
    def __init__(self, platform, name, schema=None, description=None):
        self.platform = platform
        self.name = name
        self.urn = _Urn(f"urn:dataset:{name}")
        self.description = description
        self.schema = [_Field(name) for name, _type in (schema or [])]
        self.structured_properties = {}

    def set_structured_property(self, urn, values):
        self.structured_properties[urn] = values


class _Field:
    def __init__(self, name):
        self.field_path = name
        self.tags = []

    def add_tag(self, tag):
        self.tags.append(SimpleNamespace(tag=tag))


@pytest.mark.parametrize(
    ("upstream", "downstream_count", "expected"),
    [
        (True, 3, "passed"),
        (True, 4, "passed"),
        (True, 10, "passed"),
        (False, 3, "failed"),
        (True, 0, "failed"),
        (True, 1, "failed"),
        (True, 2, "failed"),
        (False, 0, "failed"),
    ],
)
def test_live_estate_status_matrix(monkeypatch, upstream, downstream_count, expected) -> None:
    state = SimpleNamespace(upserts=[], lineage_writes=[], connection_tests=0)
    upstream_rows = [_Urn("urn:source:birth_date")] if upstream else []
    downstream_rows = [
        SimpleNamespace(urn=_Urn(f"urn:consumer:{i}")) for i in range(downstream_count)
    ]

    class Entities:
        def upsert(self, entity):
            state.upserts.append(entity)

    class Lineage:
        def add_lineage(self, **kwargs):
            state.lineage_writes.append(kwargs)

        def get_lineage(self, **kwargs):
            return upstream_rows if kwargs.get("direction") == "upstream" else downstream_rows

    class Client:
        def __init__(self, server):
            state.server = server
            self.entities = Entities()
            self.lineage = Lineage()

        def test_connection(self):
            state.connection_tests += 1

    _install(
        monkeypatch,
        {
            "datahub": _module("datahub"),
            "datahub.metadata": _module("datahub.metadata"),
            "datahub.metadata.urns": _module(
                "datahub.metadata.urns",
                DatasetUrn=lambda platform, name: _Urn(f"urn:dataset:{name}"),
            ),
            "datahub.sdk": _module("datahub.sdk", DataHubClient=Client, Dataset=_Dataset),
        },
    )
    monkeypatch.setattr(live.time, "time", lambda: 123)
    monkeypatch.setattr(live.time, "sleep", lambda _seconds: None)
    report = live.seed_and_discover("http://core")
    assert report["status"] == expected
    assert report["synthetic_only"] is True
    assert report["blast_radius"]["downstream_count"] == downstream_count
    assert state.server == "http://core"
    assert state.connection_tests == 1
    assert len(state.upserts) == 6
    assert len(state.lineage_writes) == 5


def test_live_estate_retries_eventually_consistent_lineage(monkeypatch) -> None:
    calls = {"upstream": 0, "downstream": 0}

    class Client:
        def __init__(self, server):
            self.entities = SimpleNamespace(upsert=lambda _entity: None)
            self.lineage = self

        def test_connection(self):
            pass

        def add_lineage(self, **_kwargs):
            pass

        def get_lineage(self, **kwargs):
            direction = kwargs["direction"]
            calls[direction] += 1
            ready = calls[direction] >= 3
            if direction == "upstream":
                return [_Urn("source")] if ready else []
            return [SimpleNamespace(urn=_Urn(str(i))) for i in range(3)] if ready else []

    _install(
        monkeypatch,
        {
            "datahub": _module("datahub"),
            "datahub.metadata": _module("datahub.metadata"),
            "datahub.metadata.urns": _module(
                "datahub.metadata.urns", DatasetUrn=lambda **_kwargs: _Urn("export")
            ),
            "datahub.sdk": _module("datahub.sdk", DataHubClient=Client, Dataset=_Dataset),
        },
    )
    sleeps = []
    monkeypatch.setattr(live.time, "sleep", sleeps.append)
    assert live.seed_and_discover()["status"] == "passed"
    assert sleeps == [1, 1]


class _TagUrn(str):
    def __new__(cls, name):
        return super().__new__(cls, f"urn:tag:{name}")


class _Tag:
    def __init__(self, name, **_kwargs):
        self.name = name
        self.urn = _TagUrn(name)


class _Document:
    @classmethod
    def create_document(
        cls, id, title, text, subtype, related_assets, custom_properties, show_in_global_context
    ):
        document = cls()
        document.urn = _Urn(f"urn:document:{id}")
        document.title = title
        document.text = text
        document.subtype = subtype
        document.related_assets = related_assets
        document.custom_properties = custom_properties
        document.show_in_global_context = show_in_global_context
        return document


def _governed_modules(monkeypatch, *, alter_target=False, alter_document=False):
    state = SimpleNamespace(entities={}, connection_tests=0)

    class Entities:
        def upsert(self, entity):
            state.entities[str(entity.urn)] = entity

        def get(self, urn):
            entity = state.entities[str(urn)]
            if alter_target and isinstance(entity, _Dataset):
                entity.structured_properties = {}
                entity.schema[0].tags = []
            if alter_document and isinstance(entity, _Document):
                entity.related_assets = []
            return entity

    class Client:
        def __init__(self, server):
            state.server = server
            self.entities = Entities()

        def test_connection(self):
            state.connection_tests += 1

    _install(
        monkeypatch,
        {
            "datahub": _module("datahub"),
            "datahub.metadata": _module("datahub.metadata"),
            "datahub.metadata.urns": _module("datahub.metadata.urns", TagUrn=_TagUrn),
            "datahub.sdk": _module(
                "datahub.sdk", DataHubClient=Client, Dataset=_Dataset, Document=_Document, Tag=_Tag
            ),
        },
    )
    return state


def test_governed_writeback_requires_explicit_approval() -> None:
    assert governed.publish(approved=False) == {
        "status": "awaiting_human_approval",
        "mutation_performed": False,
    }


@pytest.mark.parametrize(
    ("alter_target", "alter_document", "incident_state", "expected"),
    [
        (False, False, "ACTIVE", "published"),
        (True, False, "ACTIVE", "verification_failed"),
        (False, True, "ACTIVE", "verification_failed"),
        (False, False, "RESOLVED", "verification_failed"),
        (True, True, "RESOLVED", "verification_failed"),
    ],
)
def test_governed_writeback_reread_matrix(
    monkeypatch, alter_target, alter_document, incident_state, expected
) -> None:
    state = _governed_modules(monkeypatch, alter_target=alter_target, alter_document=alter_document)
    monkeypatch.setattr(governed.time, "time", lambda: 123)
    monkeypatch.setattr("mosaic.datahub_graphql.ensure_risk_property", lambda _server: None)
    monkeypatch.setattr("mosaic.datahub_graphql.raise_incident", lambda *_args: "urn:incident:1")
    monkeypatch.setattr(
        "mosaic.datahub_graphql.active_incidents",
        lambda *_args: [{"urn": "urn:incident:1", "status": {"state": incident_state}}],
    )
    report = governed.publish("http://core", approved=True)
    assert report["status"] == expected
    assert report["mutation_performed"] is True
    assert set(report["checks"]) == {
        "field_tag_reread",
        "structured_property_reread",
        "threat_document_reread",
        "active_incident_reread",
    }
    assert state.connection_tests == 1
    assert report["entities"]["structured_property"] == "urn:li:structuredProperty:mosaic.riskState"


class _AsyncContext:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_args):
        return False


def _install_mcp(
    monkeypatch,
    *,
    tools=None,
    search=True,
    lineage_error=False,
    mutation_error=False,
    reread_tag=True,
):
    tools = tools or {"search", "get_entities", "get_lineage", "add_tags"}

    class Client:
        def __init__(self, server):
            self.entities = SimpleNamespace(upsert=lambda _entity: None)
            self.lineage = SimpleNamespace(add_lineage=lambda **_kwargs: None)

    class Session:
        def __init__(self, *_args):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def initialize(self):
            return SimpleNamespace(serverInfo=SimpleNamespace(name="DataHub MCP", version="1"))

        async def list_tools(self):
            return SimpleNamespace(tools=[SimpleNamespace(name=name) for name in tools])

        async def call_tool(self, name, _arguments):
            if name == "search":
                results = [{"entity": {"urn": "urn:target"}}] if search else []
                return SimpleNamespace(structuredContent={"searchResults": results})
            if name == "get_lineage":
                return SimpleNamespace(
                    isError=lineage_error, structuredContent={"column": "birth_date"}
                )
            if name == "add_tags":
                return SimpleNamespace(isError=mutation_error, structuredContent={})
            content = {"tag": "Mosaic MCP verified"} if reread_tag else {}
            return SimpleNamespace(isError=False, structuredContent=content)

    _install(
        monkeypatch,
        {
            "datahub": _module("datahub"),
            "datahub.sdk": _module("datahub.sdk", DataHubClient=Client, Dataset=_Dataset, Tag=_Tag),
            "mcp": _module("mcp", ClientSession=Session),
            "mcp.client": _module("mcp.client"),
            "mcp.client.streamable_http": _module(
                "mcp.client.streamable_http",
                streamable_http_client=lambda _url: _AsyncContext((object(), object(), object())),
            ),
        },
    )

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(mcp_probe.asyncio, "sleep", no_sleep)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tools", "lineage_error", "mutation_error", "reread_tag", "expected"),
    [
        ({"search", "get_entities", "get_lineage", "add_tags"}, False, False, True, "passed"),
        ({"search", "get_entities", "get_lineage"}, False, False, True, "failed"),
        ({"search", "get_entities", "get_lineage", "add_tags"}, True, False, True, "failed"),
        ({"search", "get_entities", "get_lineage", "add_tags"}, False, True, True, "failed"),
        ({"search", "get_entities", "get_lineage", "add_tags"}, False, False, False, "failed"),
    ],
)
async def test_mcp_probe_contract_matrix(
    monkeypatch, tools, lineage_error, mutation_error, reread_tag, expected
) -> None:
    _install_mcp(
        monkeypatch,
        tools=tools,
        lineage_error=lineage_error,
        mutation_error=mutation_error,
        reread_tag=reread_tag,
    )
    report = await mcp_probe.run_probe("http://mcp", "http://core")
    assert report["status"] == expected
    assert report["server"] == {"name": "DataHub MCP", "version": "1"}
    assert report["target_urn"] == "urn:target"


@pytest.mark.asyncio
async def test_mcp_probe_fails_when_search_never_converges(monkeypatch) -> None:
    _install_mcp(monkeypatch, search=False)
    with pytest.raises(RuntimeError, match="did not find"):
        await mcp_probe.run_probe()


def test_mcp_sync_entrypoint(monkeypatch) -> None:
    async def fake_probe():
        return {"status": "passed"}

    monkeypatch.setattr(mcp_probe, "run_probe", fake_probe)
    assert mcp_probe.run() == {"status": "passed"}
