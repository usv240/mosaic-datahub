from __future__ import annotations

import json
from types import SimpleNamespace

from mosaic.final_cli import main
from mosaic.snowflake_receipt import verify_snowflake


def _environment() -> dict[str, str]:
    return {
        "SNOWFLAKE_ACCOUNT": "account",
        "SNOWFLAKE_USER": "user",
        "SNOWFLAKE_PASSWORD": "super-sensitive-value-123",
        "SNOWFLAKE_ROLE": "MOSAIC_READER",
        "SNOWFLAKE_WAREHOUSE": "MOSAIC_WH",
        "SNOWFLAKE_DATABASE": "GOVERNANCE",
        "SNOWFLAKE_SCHEMA": "EVIDENCE",
    }


class _Cursor:
    def execute(self, query):
        assert query.startswith("SELECT CURRENT_ACCOUNT()")

    def fetchall(self):
        return [("account", "user", "MOSAIC_READER", "MOSAIC_WH", "GOVERNANCE", "EVIDENCE")]

    def close(self):
        pass


class _Connection:
    def cursor(self):
        return _Cursor()

    def close(self):
        pass


def test_snowflake_receipt_hashes_context_and_never_records_secrets() -> None:
    captured = {}

    def connect(**options):
        captured.update(options)
        return _Connection()

    report = verify_snowflake(_environment(), connector=SimpleNamespace(connect=connect))
    serialized = json.dumps(report)
    assert report["status"] == "passed"
    assert report["raw_person_rows_returned"] == 0
    assert report["secrets_recorded"] is False
    assert set(report["context_sha256"]) == {
        "account",
        "user",
        "role",
        "warehouse",
        "database",
        "schema",
    }
    assert "super-sensitive-value-123" not in serialized
    assert captured["session_parameters"]["QUERY_TAG"] == "mosaic:adapter-verification"


def test_snowflake_receipt_is_actionable_without_credentials() -> None:
    report = verify_snowflake({})
    assert report["status"] == "blocked_external_credentials"
    assert "SNOWFLAKE_ACCOUNT" in report["missing"]
    assert report["raw_person_rows_returned"] == 0


def test_snowflake_receipt_sanitizes_connector_failure() -> None:
    connector = SimpleNamespace(
        connect=lambda **_options: (_ for _ in ()).throw(RuntimeError("secret account"))
    )
    report = verify_snowflake(_environment(), connector=connector)
    assert report["status"] == "failed"
    assert "secret account" not in json.dumps(report)


def test_verify_snowflake_cli_persists_blocked_receipt(monkeypatch, tmp_path, capsys) -> None:
    for name in _environment():
        monkeypatch.delenv(name, raising=False)
    output = tmp_path / "snowflake.json"
    assert main(["verify-snowflake", "--output", str(output)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "blocked_external_credentials"
    assert json.loads(output.read_text(encoding="utf-8")) == report
