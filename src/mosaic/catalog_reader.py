from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mosaic.qi_classifier import Classification, classify_column


@dataclass(frozen=True)
class ColumnOrigin:
    column: str
    upstream_urn: str
    upstream_field: str
    platform: str
    source_dataset: str
    classification: Classification


@dataclass(frozen=True)
class Convergence:
    target_urn: str
    origins: tuple[ColumnOrigin, ...]

    @property
    def families(self) -> tuple[str, ...]:
        return tuple(sorted({origin.classification.family for origin in self.origins}))

    @property
    def upstream_datasets(self) -> tuple[str, ...]:
        return tuple(sorted({origin.upstream_urn for origin in self.origins}))


@dataclass(frozen=True)
class ClassifiedField:
    column: str
    data_type: str
    classification: Classification


@dataclass(frozen=True)
class CatalogInspection:
    target_urn: str
    schema_field_count: int
    classified_fields: tuple[ClassifiedField, ...]
    dataset_upstreams: tuple[str, ...]


def _value(item: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(item, dict) and name in item:
            return item[name]
        if hasattr(item, name):
            return getattr(item, name)
    return default


def _urn_parts(urn: str) -> tuple[str, str]:
    match = re.match(r"urn:li:dataset:\(urn:li:dataPlatform:([^,]+),(.+),[^,]+\)$", urn)
    if match:
        return match.group(1), match.group(2)
    return "unknown", urn


def _is_dataset_urn(urn: str) -> bool:
    return urn.startswith("urn:li:dataset:(")


def _schema_fields(entity: Any) -> tuple[Any, ...]:
    fields = _value(entity, "schema", "fields", default=())
    if not fields:
        schema_metadata = _value(entity, "schema_metadata", "schemaMetadata")
        fields = _value(schema_metadata, "fields", default=())
    return tuple(fields or ())


def inspect_catalog_asset(client: Any, urn: str, max_hops: int = 3) -> CatalogInspection:
    """Read schema and dataset lineage once before expensive column traversal."""
    if max_hops < 1:
        raise ValueError("max_hops must be at least one")
    entity = client.entities.get(urn)
    if entity is None:
        raise LookupError(f"DataHub asset not found: {urn}")
    schema_fields = _schema_fields(entity)
    classified: list[ClassifiedField] = []
    for field in schema_fields:
        name = str(_value(field, "field_path", "fieldPath", "name", default=""))
        data_type = str(_value(field, "type", "nativeDataType", "data_type", default="unknown"))
        terms = tuple(
            str(_value(term, "name", "urn", default=term))
            for term in (_value(field, "glossary_terms", "glossaryTerms", default=()) or ())
        )
        tags = tuple(
            str(_value(tag, "name", "urn", "tag", default=tag))
            for tag in (_value(field, "tags", default=()) or ())
        )
        classification = classify_column(name, data_type, glossary_terms=terms, tags=tags)
        if classification:
            classified.append(ClassifiedField(name, data_type, classification))
    edges = client.lineage.get_lineage(
        source_urn=urn,
        direction="upstream",
        max_hops=max_hops,
    )
    upstreams = tuple(
        sorted(
            {
                upstream
                for edge in (edges or ())
                if (upstream := str(_value(edge, "urn", "source_urn", "sourceUrn", default="")))
                and upstream != urn
            }
        )
    )
    return CatalogInspection(urn, len(schema_fields), tuple(classified), upstreams)


def discover_from_urn(client: Any, urn: str, max_hops: int = 3) -> tuple[ColumnOrigin, ...]:
    """Traverse actual DataHub column lineage; never manufactures an origin."""
    if max_hops < 1:
        raise ValueError("max_hops must be at least one")
    entity = client.entities.get(urn)
    if entity is None:
        raise LookupError(f"DataHub asset not found: {urn}")
    origins: list[ColumnOrigin] = []
    for field in _schema_fields(entity):
        name = str(_value(field, "field_path", "fieldPath", "name", default=""))
        data_type = str(_value(field, "type", "nativeDataType", "data_type", default="unknown"))
        terms = tuple(
            str(_value(term, "name", "urn", default=term))
            for term in (_value(field, "glossary_terms", "glossaryTerms", default=()) or ())
        )
        tags = tuple(
            str(_value(tag, "name", "urn", "tag", default=tag))
            for tag in (_value(field, "tags", default=()) or ())
        )
        classification = classify_column(name, data_type, glossary_terms=terms, tags=tags)
        if classification is None:
            continue
        edges = client.lineage.get_lineage(
            source_urn=urn,
            source_column=name,
            direction="upstream",
            max_hops=max_hops,
        )
        for edge in edges or ():
            upstream_urn = str(_value(edge, "urn", "source_urn", "sourceUrn", default=""))
            if not upstream_urn or upstream_urn == urn or not _is_dataset_urn(upstream_urn):
                continue
            upstream_field = str(_value(edge, "column", "field", "source_column", default=name))
            platform, dataset = _urn_parts(upstream_urn)
            origins.append(
                ColumnOrigin(
                    column=name,
                    upstream_urn=upstream_urn,
                    upstream_field=upstream_field,
                    platform=platform,
                    source_dataset=dataset,
                    classification=classification,
                )
            )
    return tuple(origins)


def derive_convergence(
    client: Any,
    urn: str,
    max_hops: int = 3,
    inspection: CatalogInspection | None = None,
) -> Convergence | None:
    inspection = inspection or inspect_catalog_asset(client, urn, max_hops)
    families = {field.classification.family for field in inspection.classified_fields}
    if len(inspection.dataset_upstreams) < 2 or len(families) < 2:
        return None
    origins = discover_from_urn(client, urn, max_hops)
    families = {origin.classification.family for origin in origins}
    datasets = {origin.upstream_urn for origin in origins}
    if len(families) < 2 or len(datasets) < 2:
        return None
    return Convergence(target_urn=urn, origins=origins)
