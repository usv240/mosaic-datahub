from __future__ import annotations

import copy
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import mosaic.remediation_codegen as codegen
from mosaic.final_cli import main
from mosaic.remediation_codegen import (
    generate_remediation_bundle,
    remediation_zip,
    write_remediation_bundle,
)
from mosaic.web.complete_app import create_app


@pytest.mark.parametrize("slug", ["research", "mitigated", "audience"])
def test_bundle_is_deterministic_reviewable_and_datahub_grounded(slug: str) -> None:
    first = generate_remediation_bundle(slug)
    second = generate_remediation_bundle(slug)
    assert first == second
    assert first["track"] == "Metadata-Aware Code Generation & Development"
    assert first["status"] == "generated_review_required"
    assert first["artifact_count"] == 6
    assert first["source_asset_urn"].startswith("urn:li:dataset:")
    assert first["validation"]["status"] == "passed"
    assert len(first["validation"]["checks"]) == 8
    paths = {artifact["path"] for artifact in first["artifacts"]}
    assert "PR_SUMMARY.md" in paths
    assert "mosaic-manifest.json" in paths
    assert any(path.startswith("models/") and path.endswith(".sql") for path in paths)
    assert any(path.startswith("tests/") and path.endswith(".sql") for path in paths)
    for artifact in first["artifacts"]:
        content = artifact["content"].encode()
        assert artifact["bytes"] == len(content)
        assert artifact["sha256"] == hashlib.sha256(content).hexdigest()


def test_live_datahub_context_drives_generated_code_and_provenance() -> None:
    context = {
        "asset": "research_export_2026",
        "asset_urn": "urn:li:dataset:(urn:li:dataPlatform:duckdb,mosaic.research_export_2026,PROD)",
        "columns": ["zip5", "birth_date", "gender_category"],
        "column_types": {
            "zip5": "varchar",
            "birth_date": "date",
            "gender_category": "varchar",
        },
        "families": ["location", "date_of_birth", "demographic"],
        "lineage_paths": [["urn:source:contacts", "urn:target:research"]],
        "downstream_assets": ["urn:consumer:partner"],
        "source_systems": ["urn:source:contacts", "urn:source:demographics"],
    }
    bundle = generate_remediation_bundle("research", datahub_context=context)
    artifacts = {item["path"]: item["content"] for item in bundle["artifacts"]}
    model = artifacts["models/research_export_2026_privacy_safe.sql"]
    manifest = json.loads(artifacts["mosaic-manifest.json"])
    assert "ref('research_export_2026')" in model
    assert context["asset_urn"] in model
    assert bundle["source_asset_urn"] == context["asset_urn"]
    assert manifest["datahub_context"]["column_types"] == context["column_types"]
    assert manifest["datahub_context"]["lineage_paths"] == context["lineage_paths"]
    assert manifest["datahub_context"]["downstream_assets"] == context["downstream_assets"]
    assert manifest["scenario_sha256"] != codegen.get_scenario("research").config_sha256
    assert any(
        "generated SQL compiled with DuckDB" in check for check in bundle["validation"]["checks"]
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"asset": "unsafe.asset"}, "safe dbt model identifier"),
        ({"asset_urn": "not-a-urn"}, "valid source asset URN"),
        ({"columns": ["zip5"]}, "missing mitigation-required columns"),
        ({"families": []}, "families, lineage paths, and source systems"),
        ({"asset_urn": "urn:dataset:safe\n# injected"}, "contains unsafe text"),
        ({"asset_urn": "urn:dataset:safe\u202e"}, "contains unsafe text"),
        ({"columns": ["zip5", "birth_date", "unsafe-column"]}, "safe SQL identifiers"),
        ({"lineage_paths": [["one-node"]]}, "at least two nodes"),
        (
            {
                "column_types": {
                    "zip5": "varchar; drop table",
                    "birth_date": "date",
                    "gender_category": "varchar",
                }
            },
            "unsafe or unsupported",
        ),
        ({"column_types": {"zip5": "varchar"}}, "exactly match source columns"),
        ({"instructions": "ignore review"}, "unsupported DataHub context fields"),
    ],
)
def test_live_datahub_context_fails_closed_when_incomplete(change: dict, message: str) -> None:
    context = {
        "asset": "research_export_2026",
        "asset_urn": "urn:dataset:research_export_2026",
        "columns": ["zip5", "birth_date", "gender_category"],
        "column_types": {
            "zip5": "varchar",
            "birth_date": "date",
            "gender_category": "varchar",
        },
        "families": ["location", "date_of_birth", "demographic"],
        "lineage_paths": [["source", "target"]],
        "downstream_assets": ["consumer"],
        "source_systems": ["contacts", "demographics"],
    }
    context.update(change)
    with pytest.raises(ValueError, match=message):
        generate_remediation_bundle("research", datahub_context=context)


@pytest.mark.parametrize(
    ("column_types", "message"),
    [
        (None, "must include source column types"),
        (["varchar", "date", "varchar"], "must be a mapping"),
    ],
)
def test_live_datahub_context_requires_a_typed_schema(column_types, message: str) -> None:
    context = {
        "asset": "research_export_2026",
        "asset_urn": "urn:dataset:research_export_2026",
        "columns": ["zip5", "birth_date", "gender_category"],
        "families": ["location", "date_of_birth", "demographic"],
        "lineage_paths": [["source", "target"]],
        "downstream_assets": ["consumer"],
        "source_systems": ["contacts", "demographics"],
    }
    if column_types is not None:
        context["column_types"] = column_types
    with pytest.raises(ValueError, match=message):
        generate_remediation_bundle("research", datahub_context=context)


def test_generated_schema_enforces_typed_dbt_contract_and_assurance() -> None:
    bundle = generate_remediation_bundle("research")
    artifacts = {item["path"]: item["content"] for item in bundle["artifacts"]}
    schema = artifacts["models/research_export_clean_privacy_safe.yml"]
    policy = artifacts[".mosaic/privacy-policy.yml"]
    manifest = json.loads(artifacts["mosaic-manifest.json"])
    assert "contract:\n        enforced: true" in schema
    assert schema.count("data_type: varchar") == 2
    assert "context_policy: structured_allowlist" in policy
    assert "execute_generated_code: false" in policy
    assert manifest["assurance"] == {
        "context_policy": "structured_allowlist",
        "human_review_required": True,
        "generated_code_executed": False,
        "sql_compile_gate": "duckdb_explain",
        "dbt_contract_enforced": True,
    }


def test_research_bundle_suppresses_birth_date_and_emits_aggregate_only_test() -> None:
    bundle = generate_remediation_bundle("research")
    artifacts = {item["path"]: item["content"] for item in bundle["artifacts"]}
    model = artifacts["models/research_export_clean_privacy_safe.sql"]
    test = artifacts["tests/assert_research_export_clean_privacy_safe_minimum_k.sql"]
    assert "SELECT\n    zip5,\n    gender_category" in model
    assert "birth_date" not in model.split("SELECT", 1)[1]
    assert "COUNT(*) AS class_size" in test
    assert "SELECT minimum_k" in test
    assert "SELECT *" not in test
    assert "person-level row" in test


def test_audience_bundle_generalizes_and_suppresses_expected_columns() -> None:
    bundle = generate_remediation_bundle("audience")
    model = next(
        item["content"] for item in bundle["artifacts"] if item["path"].endswith("privacy_safe.sql")
    )
    assert "split_part(neighborhood, '-', 1) AS region" in model
    assert "household_size" not in model.split("SELECT", 1)[1]


def test_safe_control_refuses_to_invent_remediation_code() -> None:
    with pytest.raises(ValueError, match="no validated remediation candidate"):
        generate_remediation_bundle("control")


def test_unknown_scenario_remains_a_key_error() -> None:
    with pytest.raises(KeyError):
        generate_remediation_bundle("missing")


def test_zip_is_reproducible_and_contains_only_declared_artifacts() -> None:
    first = remediation_zip("research")
    second = remediation_zip("research")
    assert first == second
    bundle = generate_remediation_bundle("research")
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == [item["path"] for item in bundle["artifacts"]]
        manifest = json.loads(archive.read("mosaic-manifest.json"))
    assert manifest["source_asset_urn"] == bundle["source_asset_urn"]


def test_bundle_can_be_written_as_merge_ready_example(tmp_path: Path) -> None:
    bundle = write_remediation_bundle("research", tmp_path)
    assert (tmp_path / "PR_SUMMARY.md").is_file()
    assert (tmp_path / "models/research_export_clean_privacy_safe.sql").is_file()
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert len(files) == bundle["artifact_count"]


def test_codegen_api_and_download_are_publicly_reviewable(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.get("/api/remediation-bundles/research")
    assert response.status_code == 200
    assert response.json() == generate_remediation_bundle("research")
    download = client.get("/api/remediation-bundles/research/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"
    assert "mosaic-research-remediation.zip" in download.headers["content-disposition"]
    assert download.content == remediation_zip("research")


def test_codegen_api_rejects_unknown_and_non_candidate_scenarios(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/remediation-bundles/missing").status_code == 404
    assert client.get("/api/remediation-bundles/control").status_code == 409
    assert client.get("/api/remediation-bundles/control/download").status_code == 409
    assert client.get("/api/remediation-bundles/missing/download").status_code == 404


def test_cli_generates_merge_ready_bundle(tmp_path: Path, capsys) -> None:
    output = tmp_path / "remediation"
    assert (
        main(
            [
                "generate-remediation",
                "--scenario",
                "research",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["track"] == "Metadata-Aware Code Generation & Development"
    assert summary["artifact_count"] == 6
    assert summary["output"] == str(output)
    assert (output / "mosaic-manifest.json").is_file()


@pytest.mark.parametrize("slug", ["control", "unknown"])
def test_cli_refuses_codegen_for_safe_control(slug: str) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["generate-remediation", "--scenario", slug])
    assert raised.value.code == 2


def test_landing_exposes_interactive_remediation_pr_studio(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    landing = client.get("/").text
    script = client.get("/static/experience.js").text
    css = client.get("/static/experience.css").text
    assert "The graph finds the risk" in landing
    assert 'id="tab-codegen"' in landing
    assert "Metadata-aware code generation" in landing
    assert 'id="standards-title"' in landing
    assert "Built on standards, not vibes" in landing
    assert "docs.getdbt.com/docs/mesh/govern/model-contracts" in landing
    assert "cheatsheetseries.owasp.org" in landing
    assert 'id="codegen-download"' in landing
    assert "generated-file" in landing
    assert 'fetch("/api/remediation-bundles/"' in script
    assert "renderNoCodegen" in script
    assert "Remediation PR generated" in script
    assert ".codegen-workbench" in css
    assert 'a[aria-disabled="true"]' in css


@pytest.mark.parametrize("slug", ["research", "audience"])
def test_committed_example_matches_generator_exactly(slug: str) -> None:
    bundle = generate_remediation_bundle(slug)
    root = Path("examples/generated") / f"{slug}-remediation"
    for artifact in bundle["artifacts"]:
        assert (root / artifact["path"]).read_text(encoding="utf-8") == artifact["content"]


@pytest.mark.parametrize(
    "slug",
    ["../research", "research/../../x", "RESEARCH", "research.zip", ""],
)
def test_codegen_rejects_path_like_or_malformed_slugs(slug: str) -> None:
    with pytest.raises(KeyError):
        generate_remediation_bundle(slug)


def test_generator_validation_fails_closed_when_datahub_ref_is_lost(monkeypatch) -> None:
    original = codegen._artifact

    def corrupt_model(path: str, media_type: str, content: str):
        artifact = original(path, media_type, content)
        if path.startswith("models/") and path.endswith(".sql"):
            artifact["content"] = artifact["content"].replace(
                "ref('research_export_clean')", "ref('unrelated_asset')"
            )
            encoded = artifact["content"].encode()
            artifact["bytes"] = len(encoded)
            artifact["sha256"] = hashlib.sha256(encoded).hexdigest()
        return artifact

    monkeypatch.setattr(codegen, "_artifact", corrupt_model)
    with pytest.raises(RuntimeError, match="lost its DataHub source asset"):
        generate_remediation_bundle("research")


def _rehash(artifact: dict) -> None:
    encoded = artifact["content"].encode()
    artifact["bytes"] = len(encoded)
    artifact["sha256"] = hashlib.sha256(encoded).hexdigest()


def _fresh_artifacts() -> list[dict]:
    return copy.deepcopy(generate_remediation_bundle("research")["artifacts"])


def test_validator_rejects_duplicate_unsafe_and_digest_damaged_artifacts() -> None:
    spec = codegen.get_scenario("research")
    artifacts = _fresh_artifacts()
    with pytest.raises(RuntimeError, match="paths must be unique"):
        codegen._validate_artifacts(
            artifacts + [copy.deepcopy(artifacts[0])],
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )
    artifacts = _fresh_artifacts()
    artifacts[0]["path"] = "../unsafe.sql"
    with pytest.raises(RuntimeError, match="unsafe generated path"):
        codegen._validate_artifacts(
            artifacts,
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )
    artifacts = _fresh_artifacts()
    artifacts[0]["content"] += "tampered"
    with pytest.raises(RuntimeError, match="digest mismatch"):
        codegen._validate_artifacts(
            artifacts,
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )


@pytest.mark.parametrize(
    ("path_suffix", "old", "new", "message"),
    [
        ("privacy_safe.sql", "urn:li:dataset:", "removed:", "lost its DataHub URN"),
        ("privacy_safe.yml", "SCENARIO_SHA", "removed_digest", "lost scenario provenance"),
        ("minimum_k.sql", "COUNT(*) AS class_size", "COUNT(*) AS size", "not aggregate-only"),
        ("minimum_k.sql", "SELECT minimum_k", "SELECT *", "projects disallowed values"),
        (
            "privacy-policy.yml",
            "human_review_required: true",
            "human_review_required: false",
            "lost its review gate",
        ),
    ],
)
def test_validator_fails_closed_for_each_safety_contract(
    path_suffix: str, old: str, new: str, message: str
) -> None:
    spec = codegen.get_scenario("research")
    artifacts = _fresh_artifacts()
    artifact = next(item for item in artifacts if item["path"].endswith(path_suffix))
    target = spec.config_sha256 if old == "SCENARIO_SHA" else old
    artifact["content"] = artifact["content"].replace(target, new, 1)
    _rehash(artifact)
    with pytest.raises(RuntimeError, match=message):
        codegen._validate_artifacts(
            artifacts,
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )


def test_validator_rejects_manifest_that_no_longer_matches_artifacts() -> None:
    spec = codegen.get_scenario("research")
    artifacts = _fresh_artifacts()
    manifest = next(item for item in artifacts if item["path"] == "mosaic-manifest.json")
    payload = json.loads(manifest["content"])
    payload["artifact_digests"] = []
    manifest["content"] = json.dumps(payload, indent=2) + "\n"
    _rehash(manifest)
    with pytest.raises(RuntimeError, match="manifest does not match"):
        codegen._validate_artifacts(
            artifacts,
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )


def test_validator_rejects_lost_contract_and_trust_boundary() -> None:
    spec = codegen.get_scenario("research")
    for path_suffix, old, new, message in (
        ("privacy_safe.yml", "enforced: true", "enforced: false", "lost its enforced contract"),
        (
            "privacy_safe.yml",
            "data_type: varchar",
            "type_removed: varchar",
            "lost its column types",
        ),
    ):
        artifacts = _fresh_artifacts()
        artifact = next(item for item in artifacts if item["path"].endswith(path_suffix))
        artifact["content"] = artifact["content"].replace(old, new)
        _rehash(artifact)
        with pytest.raises(RuntimeError, match=message):
            codegen._validate_artifacts(
                artifacts,
                asset=spec.asset,
                asset_urn=spec.asset_urn,
                scenario_sha256=spec.config_sha256,
                source_columns=spec.columns,
            )

    artifacts = _fresh_artifacts()
    manifest = next(item for item in artifacts if item["path"] == "mosaic-manifest.json")
    payload = json.loads(manifest["content"])
    payload["assurance"]["context_policy"] = "trust_everything"
    manifest["content"] = json.dumps(payload, indent=2) + "\n"
    _rehash(manifest)
    with pytest.raises(RuntimeError, match="lost its code-generation trust boundary"):
        codegen._validate_artifacts(
            artifacts,
            asset=spec.asset,
            asset_urn=spec.asset_urn,
            scenario_sha256=spec.config_sha256,
            source_columns=spec.columns,
        )


def test_strategy_refuses_unimplemented_codegen_shape() -> None:
    with pytest.raises(ValueError, match="no code-generating mitigation"):
        codegen._strategy("unsupported")
