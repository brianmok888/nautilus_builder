"""TradeHUD service — read-only observational snapshot provider.

No submit_order. No TradeAction creation. No credentials.
"""

from __future__ import annotations

from packages.tradehud_contracts.mock_data import generate_snapshot
from packages.tradehud_contracts.models import TradeHudSnapshot


class TradeHudService:
    """Provides deterministic mock/replay snapshots for TradeHUD display."""

    def __init__(self, default_symbol: str = "BTCUSDT-PERP") -> None:
        self._default_symbol = default_symbol
        self._tick_count = 0

    def get_snapshot(self, symbol: str | None = None) -> TradeHudSnapshot:
        sym = symbol or self._default_symbol
        self._tick_count += 1
        # Vary seed with tick count so successive calls differ
        return generate_snapshot(symbol=sym, seed=42 + self._tick_count)

    def get_health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "mode": "mock",
            "provenance": "mock",
            "has_runtime": False,
            "has_redis": False,
            "has_postgres": False,
            "message": "TradeHUD mock snapshot service — observational only",
        }
