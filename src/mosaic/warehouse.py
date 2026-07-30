from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class WarehouseUnavailableError(RuntimeError):
    pass


class AggregateWarehouse(Protocol):
    def execute(self, query: str) -> tuple[tuple[Any, ...], ...]: ...


@dataclass
class SnowflakeAdapter:
    """Production adapter with injectable DB-API connector and no bundled credentials."""

    connection_options: dict[str, str]
    connector: Any | None = None

    def _connector(self) -> Any:
        if self.connector is not None:
            return self.connector
        try:
            import snowflake.connector  # type: ignore[import-not-found]
        except ImportError as error:
            raise WarehouseUnavailableError(
                "install datahub-mosaic[snowflake] to use the Snowflake adapter"
            ) from error
        return snowflake.connector

    def execute(self, query: str) -> tuple[tuple[Any, ...], ...]:
        connection = self._connector().connect(**self.connection_options)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                return tuple(tuple(row) for row in cursor.fetchall())
            finally:
                cursor.close()
        finally:
            connection.close()
