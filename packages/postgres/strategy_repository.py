"""Postgres-backed strategy repository. Drop-in replacement for InMemoryStrategyRepository."""
from __future__ import annotations

import json
from typing import Any

from packages.auth import ProjectScopeError, UserProjectContext
from packages.strategy_spec.models import StrategySpec


class PostgresStrategyRepository:
    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = schema

    def _table(self, name: str) -> str:
        return f"{self._schema}.{name}"

    @staticmethod
    def _lineage_id(strategy_id: str) -> str:
        return f"lineage_{strategy_id}"

    @staticmethod
    def _version_id(strategy_id: str, index: int) -> str:
        return f"{strategy_id}_v{index:03d}"

    def save(self, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object]:
        with self._conn.transaction() as tx:
            row = tx.execute(f"SELECT count(*) FROM {self._table('strategies')}").fetchone()
            count = row[0] if row else 0
            strategy_id = "strategy_001" if count == 0 else f"strategy_{count + 1:03d}"

            spec_json = json.dumps(spec.model_dump(mode="json"), sort_keys=True)
            tx.execute(
                f"INSERT INTO {self._table('strategies')} (strategy_id, strategy_lineage_id, status, latest_spec) VALUES (%s, %s, %s, %s)",
                (strategy_id, self._lineage_id(strategy_id), spec.status.value, spec_json),
            )
            tx.execute(
                f"INSERT INTO {self._table('strategy_versions')} (strategy_version_id, strategy_id, strategy_lineage_id, spec) VALUES (%s, %s, %s, %s)",
                (self._version_id(strategy_id, 1), strategy_id, self._lineage_id(strategy_id), spec_json),
            )
        return self._record(strategy_id, spec, 1)

    def save_explicit(self, strategy_id: str, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object]:
        with self._conn.transaction() as tx:
            spec_json = json.dumps(spec.model_dump(mode="json"), sort_keys=True)
            tx.execute(
                f"INSERT INTO {self._table('strategies')} (strategy_id, strategy_lineage_id, status, latest_spec) VALUES (%s, %s, %s, %s) ON CONFLICT (strategy_id) DO UPDATE SET status = EXCLUDED.status, latest_spec = EXCLUDED.latest_spec, updated_at = now()",
                (strategy_id, self._lineage_id(strategy_id), spec.status.value, spec_json),
            )
            version_id = self._version_id(strategy_id, 1)
            tx.execute(
                f"INSERT INTO {self._table('strategy_versions')} (strategy_version_id, strategy_id, strategy_lineage_id, spec) VALUES (%s, %s, %s, %s) ON CONFLICT (strategy_version_id) DO UPDATE SET spec = EXCLUDED.spec",
                (version_id, strategy_id, self._lineage_id(strategy_id), spec_json),
            )
        return self._record(strategy_id, spec, 1)

    def update_draft(self, strategy_id: str, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object] | None:
        with self._conn.transaction() as tx:
            row = tx.execute(
                f"SELECT count(*) FROM {self._table('strategy_versions')} WHERE strategy_id = %s",
                (strategy_id,),
            ).fetchone()
            version_count = row[0] if row else 0
            if version_count == 0:
                return None

            spec_json = json.dumps(spec.model_dump(mode="json"), sort_keys=True)
            tx.execute(
                f"UPDATE {self._table('strategies')} SET status = %s, latest_spec = %s, updated_at = now() WHERE strategy_id = %s",
                (spec.status.value, spec_json, strategy_id),
            )
            version_id = self._version_id(strategy_id, version_count)
            tx.execute(
                f"UPDATE {self._table('strategy_versions')} SET spec = %s WHERE strategy_version_id = %s",
                (spec_json, version_id),
            )
        return self._record(strategy_id, spec, version_count)

    def create_version(self, strategy_id: str, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object] | None:
        with self._conn.transaction() as tx:
            row = tx.execute(
                f"SELECT count(*) FROM {self._table('strategy_versions')} WHERE strategy_id = %s",
                (strategy_id,),
            ).fetchone()
            version_count = row[0] if row else 0
            if version_count == 0:
                return None

            new_version = version_count + 1
            spec_json = json.dumps(spec.model_dump(mode="json"), sort_keys=True)
            tx.execute(
                f"UPDATE {self._table('strategies')} SET status = %s, latest_spec = %s, updated_at = now() WHERE strategy_id = %s",
                (spec.status.value, spec_json, strategy_id),
            )
            tx.execute(
                f"INSERT INTO {self._table('strategy_versions')} (strategy_version_id, strategy_id, strategy_lineage_id, spec) VALUES (%s, %s, %s, %s)",
                (self._version_id(strategy_id, new_version), strategy_id, self._lineage_id(strategy_id), spec_json),
            )
        return self._record(strategy_id, spec, new_version)

    def spec_for_version(self, strategy_version_id: str, *, context: UserProjectContext | None = None) -> StrategySpec | None:
        row = self._conn.execute(
            f"SELECT spec FROM {self._table('strategy_versions')} WHERE strategy_version_id = %s",
            (strategy_version_id,),
        ).fetchone()
        if not row:
            return None
        return StrategySpec.model_validate(json.loads(row[0]))

    def list(self, *, context: UserProjectContext | None = None) -> list[dict[str, object]]:
        rows = self._conn.execute(
            f"SELECT strategy_id, strategy_lineage_id, status, latest_spec FROM {self._table('strategies')} ORDER BY created_at"
        ).fetchall()
        return [
            {
                "strategy_id": r[0],
                "strategy_lineage_id": r[1],
                "strategy_version_id": self._current_version_id(r[0]),
                "status": r[2],
                "latest_spec": json.loads(r[3]) if isinstance(r[3], str) else r[3],
            }
            for r in rows
        ]

    def detail(self, strategy_id: str, *, context: UserProjectContext | None = None) -> dict[str, object] | None:
        row = self._conn.execute(
            f"SELECT strategy_id, strategy_lineage_id, status FROM {self._table('strategies')} WHERE strategy_id = %s",
            (strategy_id,),
        ).fetchone()
        if not row:
            return None
        versions = self._conn.execute(
            f"SELECT strategy_version_id, spec FROM {self._table('strategy_versions')} WHERE strategy_id = %s ORDER BY created_at",
            (strategy_id,),
        ).fetchall()
        return {
            "strategy_id": row[0],
            "strategy_lineage_id": row[1],
            "status": row[2],
            "versions": [
                {"strategy_version_id": v[0], "spec": json.loads(v[1]) if isinstance(v[1], str) else v[1]}
                for v in versions
            ],
        }

    def update_status(self, strategy_id: str, new_status: str) -> dict[str, object] | None:
        """Promote a strategy to a new status. Returns the updated record or None."""
        row = self._conn.execute(
            f"UPDATE {self._table('strategies')} SET status = %s, updated_at = now() WHERE strategy_id = %s RETURNING strategy_id, strategy_lineage_id, status, latest_spec",
            (new_status, strategy_id),
        ).fetchone()
        if not row:
            return None
        return {
            "strategy_id": row[0],
            "strategy_lineage_id": row[1],
            "strategy_version_id": self._current_version_id(row[0]),
            "status": row[2],
            "spec": json.loads(row[3]) if isinstance(row[3], str) else row[3],
        }

    # --- Promotion and clone support ---

    _PROMOTE_MAP: dict[str, str] = {
        "backtested": "approved",
        "approved": "execution_ready",
    }

    def approve_strategy(self, strategy_id: str) -> dict[str, object] | None:
        """Promote to the next status if eligible."""
        row = self._conn.execute(
            f"SELECT status FROM {self._table('strategies')} WHERE strategy_id = %s",
            (strategy_id,),
        ).fetchone()
        if not row:
            return None
        new_status = self._PROMOTE_MAP.get(row[0])
        if not new_status:
            return None
        return self.update_status(strategy_id, new_status)

    def clone_strategy(self, strategy_id: str) -> dict[str, object] | None:
        """Clone a strategy as a new draft."""
        from packages.strategy_spec.models import StrategyStatus, StrategyStage, CreatedFrom, Provenance
        detail = self.detail(strategy_id)
        if not detail:
            return None
        latest_spec_data = detail["versions"][-1]["spec"]
        spec = StrategySpec.model_validate(latest_spec_data)
        cloned = spec.model_copy(update={
            "status": StrategyStatus.DRAFT,
            "stage": StrategyStage.DRAFT,
            "is_frozen": False,
            "provenance": Provenance(created_by=CreatedFrom.USER, parent_version_id=strategy_id),
        })
        return self.save(cloned)

    def _current_version_id(self, strategy_id: str) -> str:
        row = self._conn.execute(
            f"SELECT count(*) FROM {self._table('strategy_versions')} WHERE strategy_id = %s",
            (strategy_id,),
        ).fetchone()
        return self._version_id(strategy_id, row[0] if row else 1)

    def _record(self, strategy_id: str, spec: StrategySpec, version_index: int) -> dict[str, object]:
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "strategy_version_id": self._version_id(strategy_id, version_index),
            "status": spec.status.value,
            "spec": spec.model_dump(mode="json"),
        }
