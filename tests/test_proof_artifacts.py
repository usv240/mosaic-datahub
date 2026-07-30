from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import mosaic.benchmark as benchmark
import mosaic.fixture_replay as replay
import mosaic.scenario_registry as registry
import mosaic.web.complete_app as web
from mosaic.final_cli import main
from mosaic.runs import load_run

FIXTURE = Path("fixtures/datahub_recording")


def test_benchmark_is_exact_repeatable_and_disclosed() -> None:
    first = benchmark.run_benchmark()
    second = benchmark.run_benchmark()
    assert first["status"] == "passed"
    assert first["cases"] == 48
    assert first["metrics"] == {
        "precision": 1.0,
        "recall": 1.0,
        "critical_false_positive_rate": 0.0,
        "exact_k_agreement": 1.0,
        "zero_raw_rows_rate": 1.0,
    }
    assert first["repeatability_sha256"] == second["repeatability_sha256"]
    assert "not field accuracy" in first["disclosure"]["what_is_by_construction"]


def test_benchmark_cli_writes_artifact(tmp_path) -> None:
    output = tmp_path / "nested" / "benchmark.json"
    assert main(["benchmark", "--output", str(output)]) == 0
    assert json.loads(output.read_text())["status"] == "passed"


def test_benchmark_cli_propagates_failed_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(benchmark, "run_benchmark", lambda: {"status": "failed"})
    assert main(["benchmark", "--output", str(tmp_path / "failed.json")]) == 2


def test_recorded_fixture_passes_and_cli_replays() -> None:
    report = replay.replay_fixture(FIXTURE)
    assert report["status"] == "passed"
    assert all(report["checks"].values())
    assert all(report["integrity"].values())
    assert main(["replay-fixture", "--fixture", str(FIXTURE)]) == 0


def test_recorded_fixture_detects_tampering(tmp_path, monkeypatch) -> None:
    copied = tmp_path / "recording"
    shutil.copytree(FIXTURE, copied)
    entity = copied / "responses/entity.json"
    entity.write_text(entity.read_text().replace('"zip5"', '"zip4"', 1))
    report = replay.replay_fixture(copied)
    assert report["status"] == "failed"
    assert report["checks"]["manifest_integrity"] is False
    monkeypatch.setattr(replay, "replay_fixture", lambda _path: report)
    assert main(["replay-fixture", "--fixture", str(copied)]) == 2


def test_elevated_policy_branch(monkeypatch) -> None:
    original = registry.get_scenario("research")
    elevated = replace(original, class_sizes=(2, 3, 5, 5, 5, 5))
    monkeypatch.setattr(registry, "get_scenario", lambda _slug: elevated)
    assert registry.assess_scenario("research")["assessment"]["verdict"] == "validated_elevated"


def test_load_run_rejects_invalid_identifier(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_run(tmp_path, "../evidence")


def test_datahub_probe_reports_both_connection_outcomes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(web, "graphql", lambda *_args: {"__typename": "Query"})
    client = TestClient(web.create_app(tmp_path))
    assert client.get("/api/health/datahub?probe=true").json()["status"] == "connected"

    def unavailable(*_args):
        raise OSError("offline")

    monkeypatch.setattr(web, "graphql", unavailable)
    assert client.get("/api/health/datahub?probe=true").json()["status"] == "unavailable"
