from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from mosaic.catalog_reader import derive_convergence, discover_from_urn
from mosaic.compositional_join import AssetProfile, detect_cross_asset_risks
from mosaic.models import Assessment, Candidate, Verdict
from mosaic.query_policy import QueryPolicyError, aggregate_query, validate_aggregate_query
from mosaic.risk import exact_k_metrics
from mosaic.scenario_registry import generate_rows, list_scenarios
from mosaic.warehouse import SnowflakeAdapter, WarehouseUnavailableError


@given(st.lists(st.tuples(st.integers(0, 4), st.integers(0, 4)), min_size=1))
def test_minimum_k_cannot_increase_when_a_column_is_added(values) -> None:
    rows = tuple({"a": str(a), "b": str(b)} for a, b in values)
    assert exact_k_metrics(rows, ("a", "b")).minimum_k <= exact_k_metrics(rows, ("a",)).minimum_k


@given(st.lists(st.tuples(st.integers(0, 4), st.integers(0, 4)), min_size=1))
def test_suppression_cannot_decrease_minimum_k(values) -> None:
    rows = tuple({"a": str(a), "b": str(b)} for a, b in values)
    assert exact_k_metrics(rows, ("a",)).minimum_k >= exact_k_metrics(rows, ("a", "b")).minimum_k


@given(st.sampled_from([";", " WHERE 1=1", " LIMIT 1", " UNION SELECT 1", " -- comment"]))
def test_every_mutation_of_approved_query_is_rejected(suffix: str) -> None:
    query = aggregate_query("safe_asset", ("zip5",)) + suffix
    with pytest.raises(QueryPolicyError):
        validate_aggregate_query(query, "safe_asset", ("zip5",))


def test_scenario_specs_contain_generators_not_baked_metrics() -> None:
    for spec in list_scenarios():
        raw = json.loads((Path("src/mosaic/scenario_specs") / f"{spec.slug}.json").read_text())
        assert "class_sizes" not in raw
        if raw.get("mitigation"):
            assert "metrics" not in raw["mitigation"]
            assert "utility_retained" not in raw["mitigation"]
        assert generate_rows(spec)


class _Client:
    def __init__(self, *, sources=2, entity=True):
        fields = [
            SimpleNamespace(field_path="postal_code", type="varchar", glossary_terms=[], tags=[]),
            SimpleNamespace(field_path="birth_date", type="date", glossary_terms=[], tags=[]),
        ]
        self.entities = SimpleNamespace(
            get=lambda _urn: SimpleNamespace(schema=fields) if entity else None
        )
        self.lineage = SimpleNamespace(get_lineage=self._lineage)
        self.sources = sources

    def _lineage(self, source_column=None, **_kwargs):
        if self.sources == 0:
            return []
        if source_column is None:
            names = ["SampleHiveDataset", "SampleKafkaDataset"][: self.sources]
            return [
                SimpleNamespace(urn=f"urn:li:dataset:(urn:li:dataPlatform:hive,{name},PROD)")
                for name in names
            ]
        source = "SampleHiveDataset" if source_column == "postal_code" else "SampleKafkaDataset"
        if self.sources == 1:
            source = "SampleHiveDataset"
        return [
            SimpleNamespace(
                urn=f"urn:li:dataset:(urn:li:dataPlatform:hive,{source},PROD)",
                column=source_column,
            )
        ]


def test_external_sample_catalog_derives_multi_source_convergence() -> None:
    urn = "urn:li:dataset:(urn:li:dataPlatform:hive,SampleDashboardDataset,PROD)"
    convergence = derive_convergence(_Client(), urn)
    assert convergence is not None
    assert convergence.families == ("date_of_birth", "location")
    assert len(convergence.upstream_datasets) == 2
    assert all("Sample" in origin.source_dataset for origin in convergence.origins)


def test_single_source_and_zero_lineage_do_not_invent_convergence() -> None:
    assert derive_convergence(_Client(sources=1), "urn:sample") is None
    assert discover_from_urn(_Client(sources=0), "urn:sample") == ()


def test_catalog_reader_propagates_not_found_and_permission_errors() -> None:
    with pytest.raises(LookupError):
        discover_from_urn(_Client(entity=False), "urn:missing")
    denied = _Client()
    denied.entities.get = lambda _urn: (_ for _ in ()).throw(PermissionError("denied"))
    with pytest.raises(PermissionError):
        discover_from_urn(denied, "urn:denied")


def test_cross_asset_join_detector_finds_risk_no_single_table_contains() -> None:
    findings = detect_cross_asset_risks(
        (
            AssetProfile("urn:a", ("member_key",), ("location", "date_of_birth")),
            AssetProfile("urn:b", ("member_key",), ("demographic",)),
            AssetProfile("urn:unrelated", ("other_key",), ("financial",)),
        )
    )
    assert len(findings) == 1
    assert findings[0].combined_families == ("date_of_birth", "demographic", "location")


def test_critical_verdict_cannot_skip_adversarial_self_check() -> None:
    candidate = Candidate("urn:x", ("a",), ("location",), (("a", "b"),), True, ())
    with pytest.raises(ValueError, match="adversarial"):
        Assessment(candidate, Verdict.VALIDATED_CRITICAL, (), None, None, 0)


def test_snowflake_adapter_executes_and_closes_every_resource() -> None:
    events = []

    class Cursor:
        def execute(self, query):
            events.append(("execute", query))

        def fetchall(self):
            return [(1, 20)]

        def close(self):
            events.append(("cursor", "closed"))

    class Connection:
        def cursor(self):
            return Cursor()

        def close(self):
            events.append(("connection", "closed"))

    connector = SimpleNamespace(connect=lambda **options: Connection())
    assert SnowflakeAdapter({"account": "demo"}, connector).execute("SELECT 1") == ((1, 20),)
    assert events[-2:] == [("cursor", "closed"), ("connection", "closed")]


def test_snowflake_adapter_has_actionable_absent_dependency_error(monkeypatch) -> None:
    adapter = SnowflakeAdapter({})
    monkeypatch.setattr(adapter, "connector", None)
    import builtins

    original = builtins.__import__

    def reject(name, *args, **kwargs):
        if name.startswith("snowflake"):
            raise ImportError
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject)
    with pytest.raises(WarehouseUnavailableError, match="snowflake"):
        adapter.execute("SELECT 1")


def test_classifier_uses_ranked_catalog_evidence() -> None:
    from mosaic.qi_classifier import classify_column

    glossary = classify_column(
        "opaque_field",
        "string",
        glossary_terms=("location",),
        tags=("financial",),
    )
    tagged = classify_column("opaque_field", "string", tags=("health",))
    typed = classify_column("postal_code", "varchar")
    named = classify_column("device_identifier", "binary")
    assert glossary and (glossary.family, glossary.confidence) == ("location", 1.0)
    assert tagged and (tagged.family, tagged.confidence) == ("health", 0.9)
    assert typed and typed.confidence == 0.75
    assert named and named.confidence == 0.55


def test_organization_policy_changes_the_actual_verdict(monkeypatch, tmp_path: Path) -> None:
    from mosaic.scenario_registry import assess_scenario

    policy = tmp_path / "privacy-policy.yml"
    policy.write_text(
        json.dumps(
            {
                "policy_id": "strict-org",
                "controls": {
                    "minimum_k": 25,
                    "maximum_percent_below_k5": 0,
                    "raw_person_rows_allowed": 0,
                },
                "approval": {"required_roles": ["privacy_owner"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MOSAIC_POLICY_PATH", str(policy))
    report = assess_scenario("mitigated")
    assert report["assessment"]["verdict"] == "validated_elevated"
    assert report["policy"]["policy_id"] == "strict-org"


def test_premerge_check_gate_is_machine_actionable(capsys) -> None:
    from mosaic.final_cli import main

    assert main(["check", "--fail-on", "critical"]) == 3
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "failed"
    assert report["raw_person_rows_returned"] == 0
    assert all(item["verdict"] == "validated_critical" for item in report["findings"])


def test_benchmark_publishes_ten_thousand_column_scale_evidence() -> None:
    from mosaic.benchmark import run_benchmark

    result = run_benchmark()
    assert result["catalog_scale"]["columns"] == 10_000
    assert result["catalog_scale"]["classified_quasi_identifiers"] == 100


def test_discover_cli_handles_unreachable_datahub(monkeypatch, capsys) -> None:
    import sys
    from types import ModuleType

    from mosaic.final_cli import main

    sdk = ModuleType("datahub.sdk")

    class Client:
        def __init__(self, server):
            self.server = server

        def test_connection(self):
            raise OSError("DataHub unreachable")

    sdk.DataHubClient = Client
    monkeypatch.setitem(sys.modules, "datahub", ModuleType("datahub"))
    monkeypatch.setitem(sys.modules, "datahub.sdk", sdk)
    assert main(["discover", "--urn", "urn:external"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_discover_cli_reports_existing_catalog_evidence(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    import sys
    from types import ModuleType

    from mosaic.final_cli import main

    client = _Client()
    client.test_connection = lambda: None
    sdk = ModuleType("datahub.sdk")
    sdk.DataHubClient = lambda server: client
    monkeypatch.setitem(sys.modules, "datahub", ModuleType("datahub"))
    monkeypatch.setitem(sys.modules, "datahub.sdk", sdk)
    urn = "urn:li:dataset:(urn:li:dataPlatform:hive,ExternalSample,PROD)"
    receipt = tmp_path / "external.json"
    assert main(["discover", "--urn", urn, "--output", str(receipt)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "convergence"
    assert len(report["origins"]) == 2
    assert all(item["evidence"] for item in report["origins"])
    assert report["schema_field_count"] == 2
    assert len(report["dataset_lineage_upstreams"]) == 2
    assert report["raw_person_rows_returned"] == 0
    assert json.loads(receipt.read_text(encoding="utf-8")) == report


def test_policy_rejects_unsafe_or_incomplete_configuration(tmp_path: Path) -> None:
    from mosaic.policy import load_policy

    path = tmp_path / "bad.yml"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete or unsafe"):
        load_policy(path)


def test_row_identifier_proposal_is_visibly_rejected() -> None:
    unsafe = (
        "SELECT member_id, zip5, COUNT(*) AS equivalence_class_size "
        "FROM research_export_clean GROUP BY member_id, zip5"
    )
    with pytest.raises(QueryPolicyError, match="approved quasi-identifier"):
        validate_aggregate_query(unsafe, "research_export_clean", ("zip5",))


def test_generic_mitigation_supports_every_generalization_and_failure_path() -> None:
    from mosaic.mitigation import simulate_mitigation

    rows = (
        {"zip": "12345", "year": "1987-01-01", "age": "27", "constant": "x"},
        {"zip": "12399", "year": "1981-02-02", "age": "29", "constant": "x"},
    )
    result = simulate_mitigation(
        rows,
        ("zip", "year", "age", "constant"),
        generalize={
            "zip": {"kind": "prefix", "length": 3},
            "year": {"kind": "decade"},
            "age": {"kind": "bucket", "width": 10},
        },
    )
    assert result["metrics"]["minimum_k"] == 2
    assert result["utility_retained"] < 1
    with pytest.raises(ValueError, match="unknown columns"):
        simulate_mitigation(rows, ("zip",), drop=("missing",))
    with pytest.raises(ValueError, match="suppress every"):
        simulate_mitigation(rows, ("zip",), drop=("zip",))
    with pytest.raises(ValueError, match="unsupported generalization"):
        simulate_mitigation(rows, ("zip",), generalize={"zip": {"kind": "unknown"}})


def test_row_generator_supports_uniform_weighted_and_rejects_invalid_specs() -> None:
    from dataclasses import replace

    from mosaic.scenario_registry import generate_rows, get_scenario

    base = get_scenario("control")
    valid = replace(
        base,
        row_generator={
            "count": 3,
            "seed": 7,
            "fields": {
                "job_execution_id": {
                    "domain": ["a", "b"],
                    "distribution": "weighted",
                    "weights": [1, 0],
                }
            },
        },
    )
    assert {row["job_execution_id"] for row in generate_rows(valid)} == {"a"}
    uniform = replace(
        base,
        row_generator={
            "count": 2,
            "seed": 7,
            "fields": {"job_execution_id": {"domain": ["a"], "distribution": "uniform"}},
        },
    )
    assert len(generate_rows(uniform)) == 2
    for generator, message in (
        ({"count": 0, "fields": {}}, "invalid row generator"),
        (
            {"count": 1, "fields": {"job_execution_id": {"domain": []}}},
            "empty row-generator domain",
        ),
        (
            {
                "count": 1,
                "fields": {
                    "job_execution_id": {
                        "domain": ["a", "b"],
                        "distribution": "weighted",
                        "weights": [1],
                    }
                },
            },
            "invalid weights",
        ),
        (
            {
                "count": 1,
                "fields": {"job_execution_id": {"domain": ["a"], "distribution": "mystery"}},
            },
            "unsupported distribution",
        ),
    ):
        with pytest.raises(ValueError, match=message):
            generate_rows(replace(base, row_generator=generator))


def test_catalog_reader_accepts_mapping_and_schema_metadata_shapes() -> None:
    from mosaic.catalog_reader import discover_from_urn

    entity = {
        "schemaMetadata": {
            "fields": [
                {
                    "fieldPath": "device_id",
                    "nativeDataType": "varchar",
                    "tags": [{"name": "device"}],
                },
                {"fieldPath": "ordinary_measure", "nativeDataType": "decimal"},
            ]
        }
    }
    target = "urn:target"
    edge = {"sourceUrn": "external-urn", "field": "source_device"}
    client = SimpleNamespace(
        entities=SimpleNamespace(get=lambda _urn: entity),
        lineage=SimpleNamespace(get_lineage=lambda **_kwargs: [edge, {"urn": target}, {}]),
    )
    origins = discover_from_urn(client, target)
    assert len(origins) == 1
    assert origins[0].platform == "unknown"
    assert origins[0].upstream_field == "source_device"
    with pytest.raises(ValueError, match="max_hops"):
        discover_from_urn(client, target, 0)


def test_policy_missing_and_malformed_files_fail_closed(tmp_path: Path) -> None:
    from mosaic.policy import load_policy

    with pytest.raises(FileNotFoundError):
        load_policy(tmp_path / "missing.yml")
    malformed = tmp_path / "malformed.yml"
    malformed.write_text("not: [valid", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON-compatible YAML"):
        load_policy(malformed)


def test_packaged_reference_policy_is_safe_fallback(monkeypatch, tmp_path: Path) -> None:
    from mosaic.policy import load_policy

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MOSAIC_POLICY_PATH", raising=False)
    policy = load_policy()
    assert policy.policy_id == "mosaic-reference-compositional-privacy"
    assert policy.raw_person_rows_allowed == 0
