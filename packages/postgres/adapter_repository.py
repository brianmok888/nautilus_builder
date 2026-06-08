"""Postgres-backed adapter and instrument registry."""
from __future__ import annotations

import json
from typing import Any

from packages.adapter_registry.models import AdapterProfile
from packages.instrument_registry.service import InstrumentSelection
from packages.postgres.identifiers import postgres_table, safe_postgres_identifier


class PostgresAdapterRepository:
    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_postgres_identifier(schema)

    def _table(self, name: str) -> str:
        return postgres_table(self._schema, name)

    # --- Adapters ---

    def list_enabled_adapters(self) -> list[AdapterProfile]:
        rows = self._conn.execute(
            f"SELECT adapter_id, enabled, venue, asset_class, data_modes, execution_modes FROM {self._table('adapters')} WHERE enabled = true ORDER BY adapter_id"
        ).fetchall()
        return [
            AdapterProfile(
                adapter_id=r[0],
                enabled=r[1],
                venue=r[2],
                asset_class=r[3],
                data_modes=json.loads(r[4]) if isinstance(r[4], str) else r[4],
                execution_modes=json.loads(r[5]) if isinstance(r[5], str) else r[5],
            )
            for r in rows
        ]

    def get_adapter_profile(self, adapter_id: str) -> AdapterProfile:
        row = self._conn.execute(
            f"SELECT adapter_id, enabled, venue, asset_class, data_modes, execution_modes FROM {self._table('adapters')} WHERE adapter_id = %s",
            (adapter_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"unknown adapter: {adapter_id}")
        if not row[1]:
            raise ValueError(f"adapter disabled: {adapter_id}")
        return AdapterProfile(
            adapter_id=row[0],
            enabled=row[1],
            venue=row[2],
            asset_class=row[3],
            data_modes=json.loads(row[4]) if isinstance(row[4], str) else row[4],
            execution_modes=json.loads(row[5]) if isinstance(row[5], str) else row[5],
        )

    def upsert_adapter(self, adapter: AdapterProfile) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table('adapters')} (adapter_id, enabled, venue, asset_class, data_modes, execution_modes) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (adapter_id) DO UPDATE SET enabled = EXCLUDED.enabled, venue = EXCLUDED.venue, asset_class = EXCLUDED.asset_class, data_modes = EXCLUDED.data_modes, execution_modes = EXCLUDED.execution_modes",
            (
                adapter.adapter_id,
                adapter.enabled,
                adapter.venue,
                adapter.asset_class,
                json.dumps(adapter.data_modes),
                json.dumps(adapter.execution_modes),
            ),
        )

    # --- Instruments ---

    def search_instruments(self, *, adapter_id: str, query: str) -> list[InstrumentSelection]:
        self.get_adapter_profile(adapter_id)  # validates adapter exists + enabled
        normalized = query.upper()
        rows = self._conn.execute(
            f"SELECT instrument_id, market_type, supported_data_types, supported_timeframes, available_date_ranges FROM {self._table('instruments')} WHERE adapter_id = %s AND UPPER(instrument_id) LIKE %s",
            (adapter_id, f"%{normalized}%"),
        ).fetchall()
        return [self._row_to_instrument(r) for r in rows]

    def data_availability(self, *, adapter_id: str, instrument_id: str) -> InstrumentSelection:
        self.get_adapter_profile(adapter_id)
        row = self._conn.execute(
            f"SELECT instrument_id, market_type, supported_data_types, supported_timeframes, available_date_ranges FROM {self._table('instruments')} WHERE adapter_id = %s AND instrument_id = %s",
            (adapter_id, instrument_id),
        ).fetchone()
        if not row:
            raise ValueError(f"instrument unknown for adapter {adapter_id}: {instrument_id}")
        return self._row_to_instrument(row)

    def upsert_instrument(self, adapter_id: str, instrument: InstrumentSelection) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table('instruments')} (adapter_id, instrument_id, market_type, supported_data_types, supported_timeframes, available_date_ranges) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (adapter_id, instrument_id) DO UPDATE SET market_type = EXCLUDED.market_type, supported_data_types = EXCLUDED.supported_data_types, supported_timeframes = EXCLUDED.supported_timeframes, available_date_ranges = EXCLUDED.available_date_ranges",
            (
                adapter_id,
                instrument.instrument_id,
                instrument.market_type,
                json.dumps(instrument.supported_data_types),
                json.dumps(instrument.supported_timeframes),
                json.dumps(instrument.available_date_ranges),
            ),
        )

    @staticmethod
    def _row_to_instrument(r: tuple) -> InstrumentSelection:
        return InstrumentSelection(
            instrument_id=r[0],
            market_type=r[1],
            supported_data_types=json.loads(r[2]) if isinstance(r[2], str) else r[2],
            supported_timeframes=json.loads(r[3]) if isinstance(r[3], str) else r[3],
            available_date_ranges=json.loads(r[4]) if isinstance(r[4], str) else r[4],
        )
