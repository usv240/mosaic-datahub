from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from mosaic.query_policy import aggregate_query, validate_aggregate_query
from mosaic.scenario_registry import ScenarioSpec, assess_scenario, get_scenario, list_scenarios

DEFAULT_REPLAY = Path("fixtures/agent_transcripts/accepted.json")

PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "selected_scenario": {"type": "string"},
        "nominated_columns": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
        "pr_narrative": {"type": "string"},
    },
    "required": [
        "selected_scenario",
        "nominated_columns",
        "rationale",
        "pr_narrative",
    ],
    "additionalProperties": False,
}

Transport = Callable[[str, dict[str, Any], float], dict[str, Any]]


def _ollama_transport(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("agent endpoint must be an absolute HTTP(S) URL")
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"agent model unavailable: {error}") from error


def replay_transport(path: Path) -> Transport:
    """Replay a recorded provider envelope so judges need no local model runtime.

    The transcript is digest-checked and returned unchanged, so parsing, verification,
    and the policy veto run exactly as they do live; only the network call is replaced.
    """
    try:
        transcript = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid agent transcript: {error}") from error
    if not isinstance(transcript, dict) or transcript.get("schema_version") != 1:
        raise ValueError("unsupported agent transcript schema")
    envelope = transcript.get("response")
    if not isinstance(envelope, dict) or not isinstance(envelope.get("response"), str):
        raise ValueError("agent transcript is missing a recorded provider envelope")
    recorded = hashlib.sha256(envelope["response"].encode("utf-8")).hexdigest()
    if recorded != transcript.get("response_sha256"):
        raise ValueError("agent transcript digest does not match the recorded response")

    def transport(_endpoint: str, _payload: dict[str, Any], _timeout: float) -> dict[str, Any]:
        return envelope

    return transport


def _candidate_context(specs: Sequence[ScenarioSpec]) -> list[dict[str, Any]]:
    return [
        {
            "scenario": spec.slug,
            "asset": spec.asset,
            "asset_urn": spec.asset_urn,
            "columns": list(spec.columns),
            "families": list(spec.families),
            "source_systems": list(spec.source_systems),
            "downstream_asset_count": len(spec.downstream_assets),
        }
        for spec in specs
    ]


def _prompt(specs: Sequence[ScenarioSpec]) -> str:
    return (
        "You are the proposal-only layer of Mosaic, a metadata-aware privacy code generator. "
        "Choose the most review-worthy asset from the provided DataHub-derived context, nominate "
        "at least two listed quasi-identifier columns from distinct semantic families, explain the "
        "nomination, and draft a concise PR narrative. Do not write SQL: deterministic policy owns "
        "query construction and validation. You do not decide "
        "risk, execute SQL, or approve a change; deterministic policy will verify and may veto you. "
        "Return only JSON matching the supplied schema. Context: "
        + json.dumps(_candidate_context(specs), separators=(",", ":"))
    )


def request_proposal(
    specs: Sequence[ScenarioSpec],
    *,
    endpoint: str,
    model: str,
    timeout: float = 90,
    transport: Transport | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {
        "model": model,
        "prompt": _prompt(specs),
        "stream": False,
        "format": PROPOSAL_SCHEMA,
        "options": {"temperature": 0},
    }
    response = (transport or _ollama_transport)(endpoint, payload, timeout)
    raw = response.get("response")
    if not isinstance(raw, str):
        raise RuntimeError("agent model returned no structured response")
    try:
        proposal = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("agent model returned malformed structured output") from error
    telemetry = {
        "provider": "ollama-compatible",
        "model": str(response.get("model", model)),
        "done": bool(response.get("done", False)),
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
    }
    return proposal, telemetry


def verify_proposal(
    proposal: dict[str, Any], allowed_specs: Sequence[ScenarioSpec]
) -> dict[str, Any]:
    allowed = {spec.slug: spec for spec in allowed_specs}
    reasons: list[str] = []
    selected = proposal.get("selected_scenario")
    spec = allowed.get(selected) if isinstance(selected, str) else None
    columns_value = proposal.get("nominated_columns")
    columns = tuple(columns_value) if isinstance(columns_value, list) else ()
    if spec is None:
        reasons.append("selected scenario is outside the allowlisted DataHub context")
    else:
        if not spec.candidate:
            reasons.append("selected asset is a negative control, not a remediation candidate")
        if len(columns) < 2 or not all(isinstance(column, str) for column in columns):
            reasons.append("at least two string quasi-identifier columns must be nominated")
        elif len(columns) != len(set(columns)) or not set(columns).issubset(spec.columns):
            reasons.append(
                "nominated columns must be unique members of the catalog schema allowlist"
            )
        else:
            families = {
                spec.families[spec.columns.index(column)]
                for column in columns
                if column in spec.columns
            }
            if len(families) < 2:
                reasons.append("nominated columns must contribute at least two semantic families")
            query = aggregate_query(spec.asset, columns)
            validate_aggregate_query(query, spec.asset, columns)
    for field in ("rationale", "pr_narrative"):
        value = proposal.get(field)
        if not isinstance(value, str) or len(value.strip()) < 20:
            reasons.append(f"{field} must contain a substantive review explanation")
    deterministic = assess_scenario(spec.slug) if spec is not None else None
    return {
        "status": "vetoed" if reasons else "accepted_for_human_review",
        "policy_veto": bool(reasons),
        "veto_reasons": reasons,
        "selected_scenario": spec.slug if spec else None,
        "deterministic_assessment": deterministic,
        "raw_person_rows_returned": 0,
        "compiled_aggregate_query": (
            aggregate_query(spec.asset, columns) if spec is not None and not reasons else None
        ),
        "generated_code_executed": False,
        "mutation_performed": False,
    }


def propose_and_verify(
    scenario: str | None = None,
    *,
    endpoint: str | None = None,
    model: str | None = None,
    timeout: float = 90,
    transport: Transport | None = None,
    replay: Path | None = None,
) -> dict[str, Any]:
    specs = [get_scenario(scenario)] if scenario else list_scenarios()
    selected_endpoint = endpoint or os.environ.get(
        "MOSAIC_AGENT_ENDPOINT", "http://127.0.0.1:11434/api/generate"
    )
    selected_model = model or os.environ.get("MOSAIC_AGENT_MODEL", "mistral:latest")
    if replay is not None and transport is None:
        transport = replay_transport(replay)
    proposal, telemetry = request_proposal(
        specs,
        endpoint=selected_endpoint,
        model=selected_model,
        timeout=timeout,
        transport=transport,
    )
    if replay is not None:
        telemetry["execution"] = "replayed_recorded_response"
        telemetry["replayed_from"] = replay.as_posix()
    verification = verify_proposal(proposal, specs)
    return {
        "schema_version": 1,
        "status": verification["status"],
        "track": "Metadata-Aware Code Generation & Development",
        "model_role": "proposal_only",
        "policy_role": "deterministic_verdict_and_veto",
        "model": telemetry,
        "proposal": proposal,
        "verification": verification,
    }
