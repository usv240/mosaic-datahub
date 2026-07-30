from __future__ import annotations

import hashlib
import json

import pytest

import mosaic.complete_e2e as complete_e2e
import mosaic.datahub_graphql as gql
from mosaic.duckdb_probe import run_probe
from mosaic.runs import list_runs, record


def test_duckdb_probe_executes_the_allowlisted_aggregate() -> None:
    report = run_probe()
    assert report["status"] == "passed"
    assert report["raw_rows_returned"] == 0
    assert report["metrics"] == {
        "total_records": 120,
        "distinct_combinations": 120,
        "minimum_k": 1,
        "percent_below_5": 100.0,
    }
    assert report["query"].startswith("SELECT zip5, birth_date, gender_category")


def test_run_digest_covers_every_field_except_digest(tmp_path) -> None:
    saved = record({"unicode": "mosaïc", "nested": {"safe": True}}, tmp_path)
    digest = saved.pop("sha256")
    canonical = json.dumps(saved, sort_keys=True, separators=(",", ":")).encode()
    assert digest == hashlib.sha256(canonical).hexdigest()


def test_run_ids_are_unique_and_files_are_distinct(tmp_path) -> None:
    first = record({"number": 1}, tmp_path)
    second = record({"number": 2}, tmp_path)
    assert first["run_id"] != second["run_id"]
    assert len(list(tmp_path.glob("mosaic-*.json"))) == 2


def test_list_runs_ignores_malformed_and_unrelated_files(tmp_path) -> None:
    record({"valid": True}, tmp_path)
    (tmp_path / "mosaic-corrupt.json").write_text("{not-json", encoding="utf-8")
    (tmp_path / "other.json").write_text("{}", encoding="utf-8")
    rows = list_runs(tmp_path)
    assert len(rows) == 1
    assert rows[0]["valid"] is True


def test_list_runs_handles_absent_directory(tmp_path) -> None:
    assert list_runs(tmp_path / "missing") == []


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_graphql_builds_endpoint_headers_and_payload(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured.update(
            url=request.full_url,
            headers=request.headers,
            data=json.loads(request.data),
            timeout=timeout,
        )
        return _Response({"data": {"ok": True}})

    monkeypatch.setattr(gql, "urlopen", fake_urlopen)
    assert gql.graphql("http://datahub/", "query Q", {"x": 1}) == {"ok": True}
    assert captured["url"] == "http://datahub/api/graphql"
    assert captured["timeout"] == 20
    assert captured["data"] == {"query": "query Q", "variables": {"x": 1}}
    assert captured["headers"]["Content-type"] == "application/json"


@pytest.mark.parametrize("payload", [{"errors": ["bad"]}, {"errors": {"message": "bad"}}])
def test_graphql_surfaces_datahub_errors(monkeypatch, payload) -> None:
    monkeypatch.setattr(gql, "urlopen", lambda *_args, **_kwargs: _Response(payload))
    with pytest.raises(RuntimeError, match="bad"):
        gql.graphql("http://datahub", "query", {})


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({}, False),
        ({"structuredProperty": None}, False),
        ({"structuredProperty": {"definition": None}}, False),
        ({"structuredProperty": {"definition": {"qualifiedName": "other"}}}, False),
        ({"structuredProperty": {"definition": {"qualifiedName": "mosaic.riskState"}}}, True),
    ],
)
def test_property_ready_matrix(monkeypatch, data, expected) -> None:
    monkeypatch.setattr(gql, "graphql", lambda *_args, **_kwargs: data)
    assert gql.property_ready("server") is expected


def test_ensure_property_is_idempotent(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(gql, "property_ready", lambda _server: True)
    monkeypatch.setattr(gql, "graphql", lambda *args: calls.append(args))
    gql.ensure_risk_property("server")
    assert calls == []


def test_ensure_property_creates_and_waits_until_readable(monkeypatch) -> None:
    readiness = iter([False, False, True])
    mutations = []
    sleeps = []
    monkeypatch.setattr(gql, "property_ready", lambda _server: next(readiness))
    monkeypatch.setattr(gql, "graphql", lambda *args: mutations.append(args) or {})
    monkeypatch.setattr(gql.time, "sleep", sleeps.append)
    gql.ensure_risk_property("server")
    assert len(mutations) == 1
    assert mutations[0][2]["input"]["qualifiedName"] == "mosaic.riskState"
    assert sleeps == [1]


def test_ensure_property_fails_when_creation_never_converges(monkeypatch) -> None:
    monkeypatch.setattr(gql, "property_ready", lambda _server: False)
    monkeypatch.setattr(gql, "graphql", lambda *_args: {})
    monkeypatch.setattr(gql.time, "sleep", lambda _seconds: None)
    with pytest.raises(RuntimeError, match="not readable"):
        gql.ensure_risk_property("server")


@pytest.mark.parametrize("returned", [None, 7, {}, []])
def test_raise_incident_requires_string_urn(monkeypatch, returned) -> None:
    monkeypatch.setattr(gql, "graphql", lambda *_args: {"raiseIncident": returned})
    with pytest.raises(RuntimeError, match="incident URN"):
        gql.raise_incident("server", "target", "suffix", "document")


def test_raise_incident_returns_urn_and_sends_evidence(monkeypatch) -> None:
    captured = {}

    def fake(_server, _query, variables):
        captured.update(variables)
        return {"raiseIncident": "urn:incident:1"}

    monkeypatch.setattr(gql, "graphql", fake)
    assert gql.raise_incident("server", "target", "42", "document") == "urn:incident:1"
    assert captured["input"]["resourceUrn"] == "target"
    assert "document" in captured["input"]["description"]


def test_active_incidents_retries_then_returns(monkeypatch) -> None:
    responses = iter(
        [
            {},
            {"dataset": {"incidents": {"incidents": []}}},
            {"dataset": {"incidents": {"incidents": [{"urn": "u"}]}}},
        ]
    )
    sleeps = []
    monkeypatch.setattr(gql, "graphql", lambda *_args: next(responses))
    monkeypatch.setattr(gql.time, "sleep", sleeps.append)
    assert gql.active_incidents("server", "target") == [{"urn": "u"}]
    assert sleeps == [1, 1]


def test_active_incidents_exhaustion_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(gql, "graphql", lambda *_args: {})
    monkeypatch.setattr(gql.time, "sleep", lambda _seconds: None)
    assert gql.active_incidents("server", "target") == []


@pytest.mark.parametrize(
    ("estate_status", "aggregate_status", "rows", "writeback_status", "approved", "expected"),
    [
        ("passed", "passed", 0, "awaiting_human_approval", False, "passed"),
        ("passed", "passed", 0, "published", True, "passed"),
        ("failed", "passed", 0, "awaiting_human_approval", False, "failed"),
        ("passed", "failed", 0, "awaiting_human_approval", False, "failed"),
        ("passed", "passed", 1, "awaiting_human_approval", False, "failed"),
        ("passed", "passed", 0, "verification_failed", True, "failed"),
    ],
)
def test_complete_e2e_check_matrix(
    monkeypatch, estate_status, aggregate_status, rows, writeback_status, approved, expected
) -> None:
    monkeypatch.setattr(
        complete_e2e, "seed_and_discover", lambda _server: {"status": estate_status}
    )
    monkeypatch.setattr(
        complete_e2e,
        "aggregate_probe",
        lambda: {"status": aggregate_status, "raw_rows_returned": rows},
    )
    monkeypatch.setattr(
        complete_e2e, "publish", lambda _server, approved: {"status": writeback_status}
    )
    report = complete_e2e.run("server", approve_writeback=approved)
    assert report["status"] == expected
    assert set(report["checks"]) == {
        "datahub_convergence_and_blast_radius",
        "metadata_aware_codegen",
        "duckdb_aggregate",
        "zero_raw_rows",
        "governed_writeback_reread",
    }
