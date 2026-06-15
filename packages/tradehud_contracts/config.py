"""TradeHUD Redis adapter configuration.

All configuration is server-side only. REDIS_URL is NEVER exposed to the browser.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ─── Legacy namespace stream map (nautilus:tradehud:*) ────────────────────────

_LEGACY_STREAM_MAP: dict[str, str] = {
    "book_top": "nautilus:tradehud:book_top",
    "book_l2": "nautilus:tradehud:book_l2",
    "account": "nautilus:tradehud:account",
    "positions": "nautilus:tradehud:positions",
    "orders": "nautilus:tradehud:open_orders",
    "signal": "nautilus:tradehud:signal",
    "gate": "nautilus:tradehud:gate",
    "trade_action": "nautilus:tradehud:trade_action",
    "execution": "nautilus:tradehud:execution",
    "quant_levels": "nautilus:tradehud:quant_levels",
    "tick_to_trade": "nautilus:tradehud:tick_to_trade",
    "health": "nautilus:tradehud:runtime_health",
}

# ─── ND namespace stream map (nd.*) ────────────────────────────────────────────

_ND_STREAM_MAP: dict[str, str] = {
    "book_top": "nd.market.book_top",
    "book_l2": "nd.market.book_l2",
    "trades": "nd.market.trades",
    "bars": "nd.market.bars",
    "account": "nd.account.snapshot",
    "positions": "nd.position.snapshot",
    "orders": "nd.order.snapshot",
    "order_events": "nd.order.event",
    "signal": "nd.strategy_signal_preview",
    "gate": "nd.gate_decision",
    "trade_action": "nd.trade_action",
    "execution": "nd.execution_report",
    "quant_levels": "nd.quant_levels.context",
    "tick_to_trade": "nd.tick_to_trade.trace",
    "health": "nd.health",
}

# All logical stream names the adapter supports.
ALL_STREAM_NAMES = list(_ND_STREAM_MAP.keys())


@dataclass(frozen=True)
class TradeHudRedisConfig:
    """Immutable configuration for TradeHUD Redis Stream adapter.

    All fields are read from environment variables at construction time.
    Never exposed to the browser.
    """

    # Feed source: "mock" or "redis". Only "redis" activates the adapter.
    feed_source: str = "mock"

    # Redis connection URL (server-side only, never NEXT_PUBLIC_).
    redis_url: str | None = None

    # Stream namespace: "nd" (default), "nautilus_tradehud" (legacy), or "custom".
    stream_namespace: str = "nd"

    # Per-stream custom overrides (from TRADEHUD_STREAM_<NAME> env vars).
    stream_overrides: dict[str, str] = field(default_factory=dict)

    # XREAD block timeout in milliseconds.
    redis_block_ms: int = 1000

    # XREAD count per stream.
    redis_count: int = 100

    # Stale threshold in milliseconds.
    stream_stale_ms: int = 3000

    # Missing threshold in milliseconds.
    stream_missing_ms: int = 10000

    @property
    def is_redis_enabled(self) -> bool:
        """Redis adapter is only active when feed_source is explicitly "redis"."""
        return self.feed_source == "redis"

    @property
    def is_redis_configured(self) -> bool:
        """Redis URL is available (may not be reachable)."""
        return self.redis_url is not None

    def get_stream_map(self) -> dict[str, str]:
        """Return logical_name → redis_stream_key mapping.

        Resolution order: custom override > namespace default.
        """
        base_map = (
            _ND_STREAM_MAP
            if self.stream_namespace == "nd"
            else _LEGACY_STREAM_MAP
        )
        result = dict(base_map)
        result.update(self.stream_overrides)
        return result

    def get_redis_keys(self) -> list[str]:
        """Return the list of actual Redis stream keys to XREAD."""
        return list(self.get_stream_map().values())

    def sanitize_redis_url(self) -> str | None:
        """Return Redis URL with password redacted: redis://:password@host → redis://***@host."""
        if not self.redis_url:
            return None
        url = self.redis_url
        # redis://:password@host → redis://***@host
        # redis://user:password@host → redis://user:***@host
        import re
        return re.sub(
            r"(redis://[^:]*:)[^@]+(@)",
            r"\1***\2",
            url,
        )

    @classmethod
    def from_env(cls) -> "TradeHudRedisConfig":
        """Build config from environment variables."""
        feed_source = os.environ.get("TRADEHUD_FEED_SOURCE", "mock").lower()
        redis_url = None
        if feed_source == "redis":
            redis_url = (
                os.environ.get("TRADEHUD_REDIS_URL")
                or os.environ.get("REDIS_URL")
                or os.environ.get("REDIS_CONNECTION_STRING")
            )
        namespace = os.environ.get("TRADEHUD_STREAM_NAMESPACE", "nd").lower()
        block_ms = _to_int(os.environ.get("TRADEHUD_REDIS_BLOCK_MS"), 1000)
        count = _to_int(os.environ.get("TRADEHUD_REDIS_COUNT"), 100)
        stale_ms = _to_int(os.environ.get("TRADEHUD_STREAM_STALE_MS"), 3000)
        missing_ms = _to_int(os.environ.get("TRADEHUD_STREAM_MISSING_MS"), 10000)

        # Per-stream overrides: TRADEHUD_STREAM_BOOK_TOP, TRADEHUD_STREAM_TRADES, etc.
        overrides: dict[str, str] = {}
        for name in ALL_STREAM_NAMES:
            env_key = f"TRADEHUD_STREAM_{name.upper()}"
            val = os.environ.get(env_key)
            if val:
                overrides[name] = val

        return cls(
            feed_source=feed_source,
            redis_url=redis_url,
            stream_namespace=namespace,
            stream_overrides=overrides,
            redis_block_ms=max(100, block_ms),
            redis_count=max(1, count),
            stream_stale_ms=max(500, stale_ms),
            stream_missing_ms=max(1000, missing_ms),
        )


def _to_int(val: str | None, default: int) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
