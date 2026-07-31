from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from typing import Any

from mosaic.warehouse import SnowflakeAdapter

_REQUIRED = (
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
)
_AUTHENTICATION = (
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_PRIVATE_KEY_PATH",
    "SNOWFLAKE_AUTHENTICATOR",
)


def _digest(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def verify_snowflake(
    environment: Mapping[str, str] | None = None,
    *,
    connector: Any | None = None,
) -> dict[str, Any]:
    """Verify a scoped Snowflake identity without publishing identity or secret values."""
    env = environment if environment is not None else os.environ
    missing = [name for name in _REQUIRED if not env.get(name)]
    if not any(env.get(name) for name in _AUTHENTICATION):
        missing.append("SNOWFLAKE_PASSWORD|PRIVATE_KEY_PATH|AUTHENTICATOR")
    base: dict[str, Any] = {
        "schema_version": 1,
        "check": "snowflake_scoped_identity",
        "query_kind": "read_only_session_context",
        "raw_person_rows_returned": 0,
        "secrets_recorded": False,
    }
    if missing:
        return base | {
            "status": "blocked_external_credentials",
            "missing": missing,
            "next_command": "uv run --extra snowflake mosaic verify-snowflake --output evidence/external/snowflake-live.json",
        }
    options = {
        "account": env["SNOWFLAKE_ACCOUNT"],
        "user": env["SNOWFLAKE_USER"],
        "role": env["SNOWFLAKE_ROLE"],
        "warehouse": env["SNOWFLAKE_WAREHOUSE"],
        "database": env["SNOWFLAKE_DATABASE"],
        "schema": env["SNOWFLAKE_SCHEMA"],
        "session_parameters": {"QUERY_TAG": "mosaic:adapter-verification"},
    }
    if env.get("SNOWFLAKE_PASSWORD"):
        options["password"] = env["SNOWFLAKE_PASSWORD"]
    if env.get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        options["private_key_file"] = env["SNOWFLAKE_PRIVATE_KEY_PATH"]
    if env.get("SNOWFLAKE_AUTHENTICATOR"):
        options["authenticator"] = env["SNOWFLAKE_AUTHENTICATOR"]
    query = (
        "SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), "
        "CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
    )
    try:
        rows = SnowflakeAdapter(options, connector).execute(query)
    except Exception as error:  # Connector errors vary by optional dependency version.
        return base | {
            "status": "failed",
            "error_type": type(error).__name__,
            "error": "Snowflake rejected the scoped verification; no credential values were recorded.",
        }
    if len(rows) != 1 or len(rows[0]) != 6:
        return base | {
            "status": "failed",
            "error": "Snowflake returned an unexpected session-context shape.",
        }
    labels = ("account", "user", "role", "warehouse", "database", "schema")
    return base | {
        "status": "passed",
        "context_sha256": {
            label: _digest(value) for label, value in zip(labels, rows[0], strict=True)
        },
        "query_tag": "mosaic:adapter-verification",
    }
