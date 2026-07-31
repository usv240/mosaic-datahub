from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from mosaic.canonical import canonical_json_sha256


@dataclass(frozen=True)
class PrivacyPolicy:
    policy_id: str
    minimum_k: int
    critical_minimum_k: int
    critical_percent_below_5: float
    maximum_percent_below_k5: float
    raw_person_rows_allowed: int
    required_roles: tuple[str, ...]
    sha256: str
    source: str


def load_policy(path: Path | None = None) -> PrivacyPolicy:
    configured = os.environ.get("MOSAIC_POLICY_PATH")
    candidate = path or Path(configured or ".mosaic/privacy-policy.yml")
    if path is None and configured is None and not candidate.is_file():
        candidate = Path(__file__).with_name("default_privacy_policy.json")
    if not candidate.is_file():
        raise FileNotFoundError(f"Mosaic organization policy not found: {candidate}")
    raw = candidate.read_bytes()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("privacy policy must be JSON-compatible YAML") from error
    controls = data.get("controls", {})
    approval = data.get("approval", {})
    policy = PrivacyPolicy(
        policy_id=str(data.get("policy_id", "")),
        minimum_k=int(controls.get("minimum_k", 0)),
        critical_minimum_k=int(controls.get("critical_minimum_k", 2)),
        critical_percent_below_5=float(controls.get("critical_percent_below_5", 20)),
        maximum_percent_below_k5=float(controls.get("maximum_percent_below_k5", -1)),
        raw_person_rows_allowed=int(controls.get("raw_person_rows_allowed", -1)),
        required_roles=tuple(str(role) for role in approval.get("required_roles", ())),
        sha256=canonical_json_sha256(data),
        source=str(candidate),
    )
    if (
        not policy.policy_id
        or policy.minimum_k < 2
        or not 0 <= policy.maximum_percent_below_k5 <= 100
        or policy.raw_person_rows_allowed != 0
        or not policy.required_roles
    ):
        raise ValueError("privacy policy is incomplete or unsafe")
    return policy
