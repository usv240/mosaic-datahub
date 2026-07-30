from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    INSUFFICIENT_METADATA = "insufficient_metadata"
    SCREENING_ONLY = "screening_only"
    VALIDATED_LOW = "validated_low"
    VALIDATED_ELEVATED = "validated_elevated"
    VALIDATED_CRITICAL = "validated_critical"


@dataclass(frozen=True)
class Candidate:
    asset_urn: str
    columns: tuple[str, ...]
    families: tuple[str, ...]
    lineage_paths: tuple[tuple[str, ...], ...]
    sensitive_attribute_present: bool
    downstream_assets: tuple[str, ...]


@dataclass(frozen=True)
class RiskMetrics:
    total_records: int
    distinct_combinations: int
    minimum_k: int
    percent_below_2: float
    percent_below_5: float
    percent_below_10: float
    class_size_distribution: dict[int, int]


@dataclass(frozen=True)
class Assessment:
    candidate: Candidate
    verdict: Verdict
    reasons: tuple[str, ...]
    metrics: RiskMetrics | None
    aggregate_query: str | None
    raw_rows_returned: int
    mitigation: dict[str, Any] | None = None
    adversarial_self_check: str | None = None

    def __post_init__(self) -> None:
        if self.verdict is Verdict.VALIDATED_CRITICAL and not self.adversarial_self_check:
            raise ValueError("a critical verdict requires an adversarial false-positive self-check")

    @property
    def exit_code(self) -> int:
        return 3 if self.verdict is Verdict.VALIDATED_CRITICAL else 0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["verdict"] = self.verdict.value
        result["exit_code"] = self.exit_code
        return result
