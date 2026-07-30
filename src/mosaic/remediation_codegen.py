from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb

from mosaic.scenario_registry import assess_scenario, get_scenario


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


_CONTEXT_KEYS = {
    "asset",
    "asset_urn",
    "columns",
    "column_types",
    "families",
    "lineage_paths",
    "downstream_assets",
    "source_systems",
}
_UNSAFE_CONTEXT = re.compile(r"[\x00-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff`\[\]]")


def _safe_context_text(value: object, label: str) -> str:
    rendered = str(value)
    if not rendered or len(rendered) > 500 or _UNSAFE_CONTEXT.search(rendered):
        raise ValueError(f"DataHub context {label} contains unsafe text")
    return rendered


def _artifact(path: str, media_type: str, content: str) -> dict[str, Any]:
    normalized = content.rstrip() + "\n"
    return {
        "path": path,
        "media_type": media_type,
        "bytes": len(normalized.encode("utf-8")),
        "sha256": _digest(normalized),
        "content": normalized,
    }


def _strategy(slug: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if slug in {"research", "mitigated"}:
        return (
            ("zip5", "gender_category"),
            ("zip5", "gender_category"),
            "Suppress precise birth_date while retaining ZIP5 and demographic category.",
        )
    if slug == "audience":
        return (
            ("substr(neighborhood, 1, 3) AS region", "age_band"),
            ("region", "age_band"),
            "Generalize neighborhood to region and suppress household_size.",
        )
    raise ValueError(f"scenario {slug!r} has no code-generating mitigation")


def _validate_artifacts(
    artifacts: list[dict[str, Any]],
    *,
    asset: str,
    asset_urn: str,
    scenario_sha256: str,
    source_columns: tuple[str, ...],
) -> list[str]:
    by_path = {item["path"]: item for item in artifacts}
    if len(by_path) != len(artifacts):
        raise RuntimeError("generated artifact paths must be unique")
    for item in artifacts:
        path = Path(item["path"])
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"unsafe generated path: {path}")
        if _digest(item["content"]) != item["sha256"]:
            raise RuntimeError(f"generated digest mismatch: {path}")
    model = next(
        item
        for item in artifacts
        if item["path"].startswith("models/") and item["path"].endswith(".sql")
    )
    schema = next(
        item
        for item in artifacts
        if item["path"].startswith("models/") and item["path"].endswith(".yml")
    )
    test = next(item for item in artifacts if item["path"].startswith("tests/"))
    policy = by_path[".mosaic/privacy-policy.yml"]
    manifest = json.loads(by_path["mosaic-manifest.json"]["content"])
    if f"ref('{asset}')" not in model["content"]:
        raise RuntimeError("generated dbt model lost its DataHub source asset")
    if asset_urn not in model["content"] or asset_urn not in schema["content"]:
        raise RuntimeError("generated model contract lost its DataHub URN")
    if scenario_sha256 not in schema["content"] or scenario_sha256 not in policy["content"]:
        raise RuntimeError("generated governance files lost scenario provenance")
    if "COUNT(*) AS class_size" not in test["content"] or "MIN(class_size)" not in test["content"]:
        raise RuntimeError("generated privacy test is not aggregate-only")
    if "SELECT *" in test["content"]:
        raise RuntimeError("generated privacy test projects disallowed values")
    if "human_review_required: true" not in policy["content"]:
        raise RuntimeError("generated policy lost its review gate")
    if "contract:" not in schema["content"] or "enforced: true" not in schema["content"]:
        raise RuntimeError("generated dbt model lost its enforced contract")
    if schema["content"].count("data_type:") < 1:
        raise RuntimeError("generated dbt contract lost its column types")
    assurance = manifest.get("assurance", {})
    if assurance.get("context_policy") != "structured_allowlist" or not assurance.get(
        "human_review_required"
    ):
        raise RuntimeError("generated manifest lost its code-generation trust boundary")
    ref_pattern = re.compile(r"\{\{\s*ref\('([^']+)'\)\s*\}\}")
    compiled_model = ref_pattern.sub(r"\1", model["content"])
    compiled_model = "\n".join(
        line for line in compiled_model.splitlines() if not line.lstrip().startswith("{{ config")
    )
    compiled_test = ref_pattern.sub(r"\1", test["content"])
    columns_sql = ", ".join(f'"{column}" VARCHAR' for column in source_columns)
    model_name = Path(model["path"]).stem
    with duckdb.connect(":memory:") as connection:
        connection.execute(f'CREATE TABLE "{asset}" ({columns_sql})')
        connection.execute("EXPLAIN " + compiled_model)
        connection.execute(f'CREATE VIEW "{model_name}" AS {compiled_model}')
        connection.execute("EXPLAIN " + compiled_test)
    expected_digests = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in artifacts
        if item["path"] != "mosaic-manifest.json"
    ]
    if manifest["artifact_digests"] != expected_digests:
        raise RuntimeError("generated manifest does not match artifact digests")
    return [
        "safe relative paths and unique filenames",
        "per-file SHA-256 digests recomputed",
        "DataHub source URN and scenario digest embedded",
        "dbt refs resolved and generated SQL compiled with DuckDB",
        "aggregate-only minimum-k test structurally checked",
        "enforced typed dbt contract structurally checked",
        "structured-context trust boundary and human review checked",
        "provenance manifest gates checked",
    ]


def generate_remediation_bundle(
    slug: str, *, datahub_context: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Generate a deterministic, review-first dbt remediation bundle from DataHub context."""
    spec = get_scenario(slug)
    if not spec.candidate or not spec.mitigation:
        raise ValueError(f"scenario {slug!r} has no validated remediation candidate")
    assessment = assess_scenario(slug)["assessment"]
    context = dict(datahub_context or {})
    unknown_keys = sorted(set(context) - _CONTEXT_KEYS)
    if unknown_keys:
        raise ValueError(f"unsupported DataHub context fields: {', '.join(unknown_keys)}")
    asset = _safe_context_text(context.get("asset", spec.asset), "asset")
    asset_urn = _safe_context_text(context.get("asset_urn", spec.asset_urn), "asset_urn")
    source_columns = tuple(
        _safe_context_text(column, "column") for column in context.get("columns", spec.columns)
    )
    if context and "column_types" not in context:
        raise ValueError("DataHub context must include source column types")
    raw_types = context.get("column_types", dict(spec.column_types))
    if not isinstance(raw_types, Mapping):
        raise ValueError("DataHub context column_types must be a mapping")
    source_column_types = {
        _safe_context_text(column, "typed column"): _safe_context_text(data_type, "data type")
        for column, data_type in raw_types.items()
    }
    families = tuple(
        _safe_context_text(family, "family") for family in context.get("families", spec.families)
    )
    lineage_paths = tuple(
        tuple(_safe_context_text(node, "lineage node") for node in path)
        for path in context.get("lineage_paths", spec.lineage_paths)
    )
    downstream_assets = tuple(
        _safe_context_text(item, "downstream asset")
        for item in context.get("downstream_assets", spec.downstream_assets)
    )
    source_systems = tuple(
        _safe_context_text(item, "source system")
        for item in context.get("source_systems", spec.source_systems)
    )
    context_sha256 = (
        _digest(json.dumps(context, sort_keys=True, separators=(",", ":")))
        if context
        else spec.config_sha256
    )
    if not re.fullmatch(r"[a-z][a-z0-9_]*", asset):
        raise ValueError("DataHub context asset must map to a safe dbt model identifier")
    if not asset_urn.startswith("urn:"):
        raise ValueError("DataHub context must include a valid source asset URN")
    if not all(re.fullmatch(r"[a-z][a-z0-9_]*", column) for column in source_columns):
        raise ValueError("DataHub context columns must be safe SQL identifiers")
    if not set(spec.columns).issubset(source_columns):
        raise ValueError("DataHub context schema is missing mitigation-required columns")
    if set(source_column_types) != set(source_columns):
        raise ValueError("DataHub context types must exactly match source columns")
    if not all(
        re.fullmatch(r"[a-z][a-z0-9_]*(?:\([0-9]+(?:,[0-9]+)?\))?", data_type)
        for data_type in source_column_types.values()
    ):
        raise ValueError("DataHub context contains an unsafe or unsupported data type")
    if not families or not lineage_paths or not source_systems:
        raise ValueError("DataHub context must include families, lineage paths, and source systems")
    if any(len(path) < 2 for path in lineage_paths):
        raise ValueError("DataHub context lineage paths must contain at least two nodes")
    expressions, output_columns, strategy = _strategy(slug)
    output_column_types = {
        column: "varchar" if column == "region" else source_column_types[column]
        for column in output_columns
    }
    model_name = f"{asset}_privacy_safe"
    select_list = ",\n    ".join(expressions)
    group_list = ", ".join(output_columns)
    lineage = "\n".join(f"- `{path[0]}` -> `{path[-1]}`" for path in lineage_paths)
    downstream = "\n".join(f"- `{asset}`" for asset in downstream_assets) or "- None"

    model_sql = f"""{{{{ config(materialized='view', tags=['mosaic_privacy_remediation']) }}}}
-- Generated by Mosaic from DataHub fine-grained lineage.
-- Source asset: {asset_urn}
-- Human review is required before merge or execution.
SELECT
    {select_list}
FROM {{{{ ref('{asset}') }}}}
"""
    schema_columns = "\n".join(
        f"      - name: {column}\n        data_type: {output_column_types[column]}\n"
        "        description: Privacy-reviewed output column."
        for column in output_columns
    )
    schema_yml = f"""version: 2

models:
  - name: {model_name}
    description: >-
      Mosaic-generated shadow remediation for {spec.name}. Review before merge.
    config:
      tags: [mosaic_privacy_remediation, human_review_required]
      contract:
        enforced: true
    meta:
      datahub_source_urn: "{asset_urn}"
      mosaic_scenario_sha256: "{context_sha256}"
      minimum_k_before: {assessment["metrics"]["minimum_k"]}
      minimum_k_after: {spec.mitigation["metrics"]["minimum_k"]}
      raw_person_rows_returned: 0
    columns:
{schema_columns}
"""
    privacy_test = f"""-- dbt singular test: returns one aggregate metric only when policy fails.
-- It never projects a person-level row or quasi-identifier value.
WITH equivalence_classes AS (
    SELECT
        {group_list},
        COUNT(*) AS class_size
    FROM {{{{ ref('{model_name}') }}}}
    GROUP BY {group_list}
),
privacy_summary AS (
    SELECT MIN(class_size) AS minimum_k
    FROM equivalence_classes
)
SELECT minimum_k
FROM privacy_summary
WHERE minimum_k < 5
"""
    policy_yml = f"""schema_version: 1
policy_id: mosaic-{slug}-minimum-k
status: proposed
human_review_required: true
source:
  datahub_urn: "{asset_urn}"
  scenario_sha256: "{context_sha256}"
controls:
  minimum_k: 5
  maximum_percent_below_k5: 0.0
  raw_person_rows_allowed: 0
mitigation:
  strategy: "{strategy}"
  generated_model: "{model_name}"
generation:
  context_policy: structured_allowlist
  execute_generated_code: false
approval:
  required_roles: [privacy_reviewer, data_owner]
  writeback_after_merge: [tag, structured_property, document, incident]
"""
    pr_summary = f"""# Privacy remediation: {spec.name}

## Why this change exists

DataHub fine-grained lineage revealed {len(families)} quasi-identifier families
converging across {len(source_systems)} source systems in `{asset}`. Mosaic's
aggregate-only validation measured minimum k={assessment["metrics"]["minimum_k"]} with
zero person-level rows returned.

## Proposed code change

{strategy} The shadow result reaches minimum k={spec.mitigation["metrics"]["minimum_k"]}
with {spec.mitigation["utility_retained"] * 100:.0f}% measured utility retained in the
synthetic scenario. These thresholds are review policy, not a legal conclusion.

## DataHub context used

- Source asset: `{asset_urn}`
- Scenario digest: `{context_sha256}`
- Context trust: structured metadata allowlist; free-form instructions are rejected
- Fine-grained lineage:
{lineage}
- Downstream review boundary:
{downstream}

## Review checklist

- [ ] Data owner confirms the generated column contract.
- [ ] Privacy reviewer approves the organization-specific threshold.
- [ ] CI runs the aggregate-only minimum-k dbt test.
- [ ] Reviewer inspects downstream compatibility before merge.
- [ ] Approved result is written back to DataHub and re-read.

Generated artifacts are proposals. Mosaic does not commit, merge, or execute them.
"""

    artifacts = [
        _artifact(f"models/{model_name}.sql", "text/sql", model_sql),
        _artifact(f"models/{model_name}.yml", "application/yaml", schema_yml),
        _artifact(f"tests/assert_{model_name}_minimum_k.sql", "text/sql", privacy_test),
        _artifact(".mosaic/privacy-policy.yml", "application/yaml", policy_yml),
        _artifact("PR_SUMMARY.md", "text/markdown", pr_summary),
    ]
    manifest = {
        "schema_version": 1,
        "generator": "Mosaic DataHub remediation codegen",
        "track": "Metadata-Aware Code Generation & Development",
        "scenario": slug,
        "source_asset_urn": asset_urn,
        "scenario_sha256": context_sha256,
        "assurance": {
            "context_policy": "structured_allowlist",
            "human_review_required": True,
            "generated_code_executed": False,
            "sql_compile_gate": "duckdb_explain",
            "dbt_contract_enforced": True,
        },
        "datahub_context": {
            "column_types": source_column_types,
            "families": list(families),
            "lineage_paths": [list(path) for path in lineage_paths],
            "downstream_assets": list(downstream_assets),
        },
        "artifact_digests": [
            {"path": item["path"], "sha256": item["sha256"]} for item in artifacts
        ],
    }
    artifacts.append(
        _artifact("mosaic-manifest.json", "application/json", json.dumps(manifest, indent=2))
    )
    bundle_sha256 = _digest(
        json.dumps(
            [(item["path"], item["sha256"]) for item in artifacts],
            separators=(",", ":"),
        )
    )
    checks = _validate_artifacts(
        artifacts,
        asset=asset,
        asset_urn=asset_urn,
        scenario_sha256=context_sha256,
        source_columns=source_columns,
    )
    return {
        "schema_version": 1,
        "track": "Metadata-Aware Code Generation & Development",
        "scenario": slug,
        "status": "generated_review_required",
        "source_asset_urn": asset_urn,
        "strategy": strategy,
        "bundle_sha256": bundle_sha256,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "validation": {
            "status": "passed",
            "checks": checks,
        },
    }


def remediation_zip(slug: str) -> bytes:
    bundle = generate_remediation_bundle(slug)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for artifact in bundle["artifacts"]:
            info = zipfile.ZipInfo(artifact["path"], date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            archive.writestr(info, artifact["content"].encode("utf-8"))
    return buffer.getvalue()


def write_remediation_bundle(slug: str, output: Path) -> dict[str, Any]:
    bundle = generate_remediation_bundle(slug)
    for artifact in bundle["artifacts"]:
        target = output / artifact["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact["content"], encoding="utf-8")
    return bundle
