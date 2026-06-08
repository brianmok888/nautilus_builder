from __future__ import annotations

from typing import Any

import pytest

import scripts.seed_builder_demo_data as seed_script


class FailingStrategyRepository:
    def __init__(self, conn: object, schema: str = "builder") -> None:
        self.conn = conn
        self.schema = schema

    def save_explicit(self, strategy_id: str, spec: object, *, context: object | None = None) -> dict[str, object]:
        raise RuntimeError(f"unexpected seed failure for {strategy_id}")


class NoopConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.executed.append((sql, params))


def test_seed_demo_strategies_pg_does_not_swallow_unexpected_save_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = NoopConnection()
    monkeypatch.setattr(seed_script, "PostgresStrategyRepository", FailingStrategyRepository)

    with pytest.raises(RuntimeError, match="unexpected seed failure"):
        seed_script.seed_demo_strategies_pg(conn)

    assert conn.executed == []
