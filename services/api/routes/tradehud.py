"""TradeHUD API routes — read-only observational endpoints.

Read-only observational data. No order execution authority. No credentials.
"""

from __future__ import annotations

from packages.tradehud_contracts.config import TradeHudRedisConfig
from packages.tradehud_contracts.service import TradeHudService

_service: TradeHudService | None = None


def _get_service() -> TradeHudService:
    global _service
    if _service is None:
        _service = TradeHudService()
    return _service


def tradehud_snapshot_payload(symbol: str | None = None) -> dict:
    """GET /api/tradehud/snapshot — observational snapshot."""
    svc = _get_service()
    snapshot = svc.get_snapshot(symbol)
    return snapshot.model_dump(mode="json")


def tradehud_health_payload() -> dict:
    """GET /api/tradehud/health — service health.

    Includes Redis adapter status when TRADEHUD_FEED_SOURCE=redis.
    Never exposes credentials.
    """
    svc = _get_service()
    health = svc.get_health()
    config = TradeHudRedisConfig.from_env()

    result = dict(health)
    result["feed_source"] = config.feed_source
    result["redis_configured"] = config.is_redis_configured
    result["redis_connected"] = False  # Updated if adapter is active
    result["stream_namespace"] = config.stream_namespace
    result["mode"] = "observational"

    # Sanitize Redis URL — never expose password
    if config.is_redis_configured:
        result["redis_url_sanitized"] = config.sanitize_redis_url()
    else:
        result["redis_url_sanitized"] = None

    # Never return raw credentials
    for key in list(result.keys()):
        if any(bad in key.lower() for bad in ("password", "secret", "token", "redis_url", "postgres_url", "database_url")):
            if key != "redis_url_sanitized":
                del result[key]

    return result


def tradehud_replay_payload(symbol: str | None = None) -> dict:
    """GET /api/tradehud/events/replay — deterministic replay events."""
    svc = _get_service()
    snapshot = svc.get_snapshot(symbol)
    events: list[dict] = []
    if snapshot.book_top:
        events.append({"type": "BOOK_TOP", "payload": snapshot.book_top.model_dump(mode="json")})
    if snapshot.book_l2:
        events.append({"type": "BOOK_L2", "payload": snapshot.book_l2.model_dump(mode="json")})
    if snapshot.trades:
        for t in snapshot.trades[-10:]:
            events.append({"type": "TRADE", "payload": t.model_dump(mode="json")})
    if snapshot.latest_signal_preview:
        events.append({"type": "SIGNAL_PREVIEW", "payload": snapshot.latest_signal_preview.model_dump(mode="json")})
    if snapshot.latest_gate_decision:
        events.append({"type": "GATE_DECISION", "payload": snapshot.latest_gate_decision.model_dump(mode="json")})
    if snapshot.latest_trade_action:
        events.append({"type": "TRADE_ACTION", "payload": snapshot.latest_trade_action.model_dump(mode="json")})
    if snapshot.latest_execution_report:
        events.append({"type": "EXECUTION_REPORT", "payload": snapshot.latest_execution_report.model_dump(mode="json")})
    if snapshot.account:
        events.append({"type": "ACCOUNT", "payload": snapshot.account.model_dump(mode="json")})
    return {"events": events, "provenance": "mock"}
