from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mosaic.models import Assessment


class ApprovalRequiredError(PermissionError):
    pass


@dataclass
class InMemoryCatalog:
    """Deterministic stand-in used to test proposal/publish/re-read semantics."""

    records: dict[str, dict[str, Any]] = field(default_factory=dict)

    def write(self, urn: str, record: dict[str, Any]) -> None:
        self.records[urn] = record

    def read(self, urn: str) -> dict[str, Any] | None:
        return self.records.get(urn)


def build_proposal(assessment: Assessment) -> dict[str, Any]:
    metrics = assessment.metrics
    if metrics is None:
        raise ValueError("cannot write back an assessment without exact metrics")
    return {
        "asset_urn": assessment.candidate.asset_urn,
        "type": "mosaic_privacy_threat_model",
        "properties": {
            "mosaic.riskState": assessment.verdict.value,
            "mosaic.minimumK": metrics.minimum_k,
            "mosaic.smallClassPercentBelow5": metrics.percent_below_5,
            "mosaic.assessorVersion": "0.1.0",
        },
        "document": {
            "title": "Mosaic privacy threat model",
            "downstream_assets": list(assessment.candidate.downstream_assets),
            "aggregate_query": assessment.aggregate_query,
            "raw_rows_returned": assessment.raw_rows_returned,
        },
        "requires_reviewer_approval": True,
    }


def publish_proposal(
    catalog: InMemoryCatalog, proposal: dict[str, Any], *, approved: bool
) -> dict[str, Any]:
    if not approved:
        raise ApprovalRequiredError("refusing catalog write: reviewer approval is required")
    urn = str(proposal["asset_urn"])
    catalog.write(urn, proposal)
    reread = catalog.read(urn)
    return {"status": "published", "reread_verified": reread == proposal, "target_urn": urn}
