from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetProfile:
    urn: str
    join_keys: tuple[str, ...]
    families: tuple[str, ...]


@dataclass(frozen=True)
class CrossAssetRisk:
    left_urn: str
    right_urn: str
    shared_keys: tuple[str, ...]
    combined_families: tuple[str, ...]


def detect_cross_asset_risks(assets: tuple[AssetProfile, ...]) -> tuple[CrossAssetRisk, ...]:
    """Find re-identification combinations that exist only after joining two assets."""
    findings = []
    for index, left in enumerate(assets):
        for right in assets[index + 1 :]:
            shared = tuple(sorted(set(left.join_keys) & set(right.join_keys)))
            families = tuple(sorted(set(left.families) | set(right.families)))
            adds_context = bool(set(left.families) - set(right.families)) and bool(
                set(right.families) - set(left.families)
            )
            if shared and len(families) >= 2 and adds_context:
                findings.append(CrossAssetRisk(left.urn, right.urn, shared, families))
    return tuple(findings)
