"""TradeHUD Redis stream normalizers — parse Redis stream entries into models.

Extracted from redis_adapter.py to separate parsing/normalization concerns from
the Redis connection/IO concerns. Behavior is identical; this module is the new
home for the `_parse_*` functions, the `_PARSERS` dispatch table, and
`parse_stream_entry`.
"""

from __future__ import annotations

import time
from typing import Any

from packages.tradehud_contracts.normalizer import (
    parse_stream_fields,
    to_optional_float,
    to_optional_int,
    to_optional_str,
    unwrap_payload,
    detect_force_liquidation,
    detect_trade_flags,
)
from packages.tradehud_contracts.models import (
    AccountSnapshotModel,
    BookLevelModel,
    ExecutionReportModel,
    GateDecisionModel,
    MarketBookL2Model,
    MarketBookTopModel,
    MarketTradeModel,
    OpenOrderSnapshotModel,
    PositionSnapshotModel,
    QuantLevelModel,
    QuantLevelsContextModel,
    RuntimeHealthModel,
    LaneHealthModel,
    StrategySignalPreviewModel,
    TickToTradeTraceModel,
    TradeActionEvidenceModel,
)

def _ns() -> int:
    return int(time.time() * 1_000_000_000)


def _parse_book_top(data: dict[str, Any]) -> MarketBookTopModel | None:
    """Parse nd.public_quote_tick payload.

    ND shape: {instrument_id, bid, ask, bid_size, ask_size, ts_event_ns}
    """
    # ND uses "bid"/"ask" keys (not "bid_price"/"ask_price")
    bid = to_optional_float(data.get("bid")) or to_optional_float(data.get("bid_price"))
    ask = to_optional_float(data.get("ask")) or to_optional_float(data.get("ask_price"))
    if bid is None or ask is None:
        return None  # Missing critical fields — not zero-filled
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return MarketBookTopModel(
        symbol=to_optional_str(data.get("instrument_id")) or to_optional_str(data.get("symbol")) or "UNKNOWN",
        bid_price=bid,
        ask_price=ask,
        bid_size=to_optional_float(data.get("bid_size")),
        ask_size=to_optional_float(data.get("ask_size")),
        mid_price=to_optional_float(data.get("mid_price")) or ((bid + ask) / 2),
        spread=to_optional_float(data.get("spread")) or (ask - bid),
        spread_bps=to_optional_float(data.get("spread_bps")),
        microprice=to_optional_float(data.get("microprice")) or ((bid + ask) / 2),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_book_l2(data: dict[str, Any]) -> MarketBookL2Model | None:
    """Parse nd.orderbook_hot_view.tui_state payload.

    ND shape: {event_type, schema_version, book_view: {venue, instrument_id,
    best_bid, best_ask, mid_price, spread_bps, bid_depth_top5, ask_depth_top5, ...}}
    """
    # Unwrap ND hot_view nested "book_view"
    bv = data.get("book_view")
    if isinstance(bv, dict):
        data = {**bv, **{k: v for k, v in data.items() if k not in ("book_view",)}}

    best_bid = to_optional_float(data.get("best_bid"))
    best_ask = to_optional_float(data.get("best_ask"))
    bid_depth_raw = data.get("bid_depth_top5", [])
    ask_depth_raw = data.get("ask_depth_top5", [])
    bids: list[BookLevelModel] = []
    asks: list[BookLevelModel] = []

    # If depth arrays present, parse them
    for b in bid_depth_raw if isinstance(bid_depth_raw, list) else []:
        bp = to_optional_float(b) if not isinstance(b, dict) else to_optional_float(b.get("price"))
        bs = to_optional_float(b.get("size")) if isinstance(b, dict) else None
        if bp is not None:
            bids.append(BookLevelModel(price=bp, size=bs or 0.0, source="redis"))
    for a in ask_depth_raw if isinstance(ask_depth_raw, list) else []:
        ap = to_optional_float(a) if not isinstance(a, dict) else to_optional_float(a.get("price"))
        asz = to_optional_float(a.get("size")) if isinstance(a, dict) else None
        if ap is not None:
            asks.append(BookLevelModel(price=ap, size=asz or 0.0, source="redis"))

    # Backward compat: parse legacy bids/asks arrays if depth arrays were empty
    if not bids:
        bids_raw = data.get("bids", [])
        for b in bids_raw if isinstance(bids_raw, list) else []:
            bp = to_optional_float(b.get("price")) if isinstance(b, dict) else to_optional_float(b)
            bs = to_optional_float(b.get("size")) if isinstance(b, dict) else None
            if bp is not None:
                bids.append(BookLevelModel(price=bp, size=bs or 0.0, source="redis"))
    if not asks:
        asks_raw = data.get("asks", [])
        for a in asks_raw if isinstance(asks_raw, list) else []:
            ap = to_optional_float(a.get("price")) if isinstance(a, dict) else to_optional_float(a)
            asz = to_optional_float(a.get("size")) if isinstance(a, dict) else None
            if ap is not None:
                asks.append(BookLevelModel(price=ap, size=asz or 0.0, source="redis"))

    # If no depth arrays but best_bid/best_ask present, synthesize top-of-book
    if not bids and best_bid is not None:
        bids.append(BookLevelModel(price=best_bid, size=0.0, source="redis"))
    if not asks and best_ask is not None:
        asks.append(BookLevelModel(price=best_ask, size=0.0, source="redis"))

    if not bids and not asks:
        return None

    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        # ND hot_view may not carry ts_event_ns; fall back to now
        ts = _ns()

    return MarketBookL2Model(
        symbol=to_optional_str(data.get("instrument_id")) or to_optional_str(data.get("symbol")) or "UNKNOWN",
        bids=bids,
        asks=asks,
        spread=to_optional_float(data.get("spread")) or (best_ask - best_bid if best_bid and best_ask else 0.0),
        spread_bps=to_optional_float(data.get("spread_bps")),
        microprice=to_optional_float(data.get("microprice")),
        top5_imbalance=to_optional_float(data.get("top5_imbalance")),
        checksum=to_optional_str(data.get("checksum")),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_trade(data: dict[str, Any]) -> MarketTradeModel | None:
    data = unwrap_payload(data)
    price = to_optional_float(data.get("price"))
    qty = to_optional_float(data.get("qty"))
    ts = to_optional_int(data.get("ts_event_ns"))

    # Required fields — missing price/qty/ts = invalid record
    if price is None or qty is None or ts is None:
        return None

    is_liq, liq_side = detect_force_liquidation(data)
    flags = detect_trade_flags(data)
    side_raw = to_optional_str(data.get("side")) or "unknown"
    aggressor_raw = to_optional_str(data.get("aggressor")) or "unknown"

    return MarketTradeModel(
        trade_id=to_optional_str(data.get("trade_id"))
        or f"{ts or _ns()}-{price}",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        price=price,
        qty=qty,
        notional=to_optional_float(data.get("notional")) or (price * qty),
        side=side_raw.lower() if side_raw.lower() in ("buy", "sell") else "buy",
        aggressor=aggressor_raw.lower() if aggressor_raw.lower() in ("buy", "sell") else "unknown",
        source="redis",
        is_large_trade=flags["is_large_trade"],
        is_sweep=flags["is_sweep"],
        is_liquidation=is_liq,
        liq_side=liq_side,  # type: ignore
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_account(data: dict[str, Any]) -> AccountSnapshotModel | None:
    """Parse nd.state_bundle payload (account_state sub-dict) or legacy account snapshot.

    ND shape: {strategy_id, account_state: {balance, equity, ...}, micro_signals: {...}, ...}
    """
    # Unwrap ND state_bundle
    acct = data.get("account_state")
    if isinstance(acct, dict):
        data = acct

    bal = to_optional_float(data.get("balance"))
    if bal is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns")) or to_optional_int(data.get("bundle_ts_ns"))
    if ts is None:
        # state_bundle may carry bundle_ts as ISO string — try timestamp from that
        ts = _ns()
    return AccountSnapshotModel(
        account_id=to_optional_str(data.get("account_id")) or to_optional_str(data.get("strategy_id")) or "unknown",
        venue=to_optional_str(data.get("venue")) or "UNKNOWN",
        balance=bal,
        equity=to_optional_float(data.get("equity")) or bal,
        available_margin=to_optional_float(data.get("available_margin")),
        margin_used=to_optional_float(data.get("margin_used")),
        unrealized_pnl=to_optional_float(data.get("unrealized_pnl")),
        realized_pnl=to_optional_float(data.get("realized_pnl")),
        currency=to_optional_str(data.get("currency")) or "USDT",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_positions(data: dict[str, Any]) -> list[PositionSnapshotModel]:
    """Parse positions from nd.state_bundle or legacy position snapshot.

    ND state_bundle may carry positions inside account_state or micro_signals.
    """
    # Unwrap ND state_bundle
    acct = data.get("account_state")
    if isinstance(acct, dict):
        data = acct

    raw = data.get("positions", [])
    if isinstance(raw, str):
        import json as _json
        try:
            raw = _json.loads(raw)
        except Exception:
            return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        # ND state_bundle may not have positions array — return empty
        return []
    ts_fallback = _ns()
    positions = []
    for p in raw:
        qty = to_optional_float(p.get("qty"))
        if qty is None:
            continue
        ts = to_optional_int(p.get("ts_event_ns")) or ts_fallback
        positions.append(PositionSnapshotModel(
            symbol=to_optional_str(p.get("symbol")) or "UNKNOWN",
            venue=to_optional_str(p.get("venue")) or "UNKNOWN",
            side=to_optional_str(p.get("side")) or "flat",
            qty=qty,
            entry_price=to_optional_float(p.get("entry_price")),
            mark_price=to_optional_float(p.get("mark_price")),
            unrealized_pnl=to_optional_float(p.get("unrealized_pnl")),
            realized_pnl=to_optional_float(p.get("realized_pnl")),
            margin=to_optional_float(p.get("margin")),
            ts_event_ns=ts,
            source_available=True,
            last_update_ts_ns=ts,
            receive_ts_ns=_ns(),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        ))
    return positions


def _parse_open_orders(data: dict[str, Any]) -> list[OpenOrderSnapshotModel]:
    raw = data.get("orders", data)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    orders = []
    for o in raw:
        price = to_optional_float(o.get("price"))
        if price is None:
            continue
        ts = to_optional_int(o.get("ts_event_ns"))
        if ts is None:
            continue
        qty = to_optional_float(o.get("qty"))
        if qty is None:
            continue
        filled_qty = to_optional_float(o.get("filled_qty"))
        orders.append(OpenOrderSnapshotModel(
            order_id=to_optional_str(o.get("order_id")) or "unknown",
            client_order_id=to_optional_str(o.get("client_order_id")) or "unknown",
            symbol=to_optional_str(o.get("symbol")) or "UNKNOWN",
            venue=to_optional_str(o.get("venue")) or "UNKNOWN",
            side=to_optional_str(o.get("side")) or "buy",
            order_type=to_optional_str(o.get("order_type")) or "LIMIT",
            price=price,
            qty=qty,
            filled_qty=filled_qty if filled_qty is not None else 0.0,
            status=to_optional_str(o.get("status")) or "LIVE",
            ts_event_ns=ts,
            source_available=True,
            last_update_ts_ns=ts,
            receive_ts_ns=_ns(),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        ))
    return orders


def _parse_signal(data: dict[str, Any]) -> StrategySignalPreviewModel | None:
    conf = to_optional_float(data.get("confidence_score"))
    if conf is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return StrategySignalPreviewModel(
        signal_id=to_optional_str(data.get("signal_id")) or "unknown",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        feature_hash=to_optional_str(data.get("feature_hash")) or "",
        context_hash=to_optional_str(data.get("context_hash")) or "",
        policy_hash=to_optional_str(data.get("policy_hash")) or "",
        graph_trace_hash=to_optional_str(data.get("graph_trace_hash")) or "",
        confidence_score=conf,
        direction=to_optional_str(data.get("direction")) or "flat",
        target_hint=to_optional_float(data.get("target_hint")),
        invalidation_hint=to_optional_float(data.get("invalidation_hint")),
        size_hint=to_optional_float(data.get("size_hint")),
        preview_note=to_optional_str(data.get("preview_note")) or "Preview only — NOT EXECUTABLE",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_gate(data: dict[str, Any]) -> GateDecisionModel | None:
    decision = to_optional_str(data.get("decision"))
    if decision is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return GateDecisionModel(
        decision_id=to_optional_str(data.get("decision_id")) or "unknown",
        decision=decision,
        first_blocking_gate=to_optional_str(data.get("first_blocking_gate")),
        reason_code=to_optional_str(data.get("reason_code")) or "",
        confidence_delta=to_optional_float(data.get("confidence_delta")),
        size_modifier=to_optional_float(data.get("size_modifier")) or 1.0,
        target_hint=to_optional_float(data.get("target_hint")),
        invalidation_hint=to_optional_float(data.get("invalidation_hint")),
        gate_decision_hash=to_optional_str(data.get("gate_decision_hash")) or "",
        source_signal_hash=to_optional_str(data.get("source_signal_hash")) or "",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_trade_action(data: dict[str, Any]) -> TradeActionEvidenceModel | None:
    action = to_optional_str(data.get("action"))
    if action is None:
        return None
    price = to_optional_float(data.get("price"))
    qty = to_optional_float(data.get("qty"))
    ts = to_optional_int(data.get("ts_event_ns"))
    trade_action_hash = to_optional_str(data.get("trade_action_hash"))
    source_gate_decision_hash = to_optional_str(data.get("source_gate_decision_hash"))
    if price is None or qty is None or ts is None:
        return None
    if not trade_action_hash:
        return None
    if not source_gate_decision_hash:
        return None
    return TradeActionEvidenceModel(
        action_id=to_optional_str(data.get("action_id")) or "unknown",
        action=action,
        side=to_optional_str(data.get("side")) or "buy",
        price=price,
        qty=qty,
        trade_action_hash=trade_action_hash,
        source_gate_decision_hash=source_gate_decision_hash,
        created_by=to_optional_str(data.get("created_by")) or "run_gate_engine",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_execution(data: dict[str, Any]) -> ExecutionReportModel | None:
    status = to_optional_str(data.get("status"))
    if status is None:
        return None
    submit_ts = to_optional_int(data.get("submit_ts_ns"))
    if submit_ts is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return ExecutionReportModel(
        report_id=to_optional_str(data.get("report_id")) or "unknown",
        status=status,
        exchange_order_id=to_optional_str(data.get("exchange_order_id")),
        client_order_id=to_optional_str(data.get("client_order_id")) or "unknown",
        trade_action_hash=to_optional_str(data.get("trade_action_hash")) or "",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        side=to_optional_str(data.get("side")) or "buy",
        filled_qty=to_optional_float(data.get("filled_qty")) or 0,
        avg_fill_price=to_optional_float(data.get("avg_fill_price")),
        submit_ts_ns=submit_ts,
        ack_ts_ns=to_optional_int(data.get("ack_ts_ns")),
        fill_ts_ns=to_optional_int(data.get("fill_ts_ns")),
        submit_to_ack_us=to_optional_int(data.get("submit_to_ack_us")),
        ack_to_fill_us=to_optional_int(data.get("ack_to_fill_us")),
        rejection_reason=to_optional_str(data.get("rejection_reason")),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_quant_levels(data: dict[str, Any]) -> QuantLevelsContextModel | None:
    levels_raw = data.get("levels", [])
    if not levels_raw:
        return None
    levels = []
    for level in levels_raw:
        lp = to_optional_float(level.get("price"))
        if lp is None:
            continue
        levels.append(QuantLevelModel(
            label=level.get("label", ""),
            price=lp,
            kind=level.get("kind", "pivot"),
        ))
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return QuantLevelsContextModel(
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        levels=levels,
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_tick_to_trade(data: dict[str, Any]) -> TickToTradeTraceModel | None:
    total = to_optional_int(data.get("total_tick_to_trade_us"))
    if total is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    tick_recv = to_optional_int(data.get("tick_receive_ts_ns"))
    sig_ts = to_optional_int(data.get("signal_ts_ns"))
    gate_ts = to_optional_int(data.get("gate_ts_ns"))
    exec_ts = to_optional_int(data.get("execution_ts_ns"))
    if any(v is None for v in (tick_recv, sig_ts, gate_ts, exec_ts)):
        return None
    return TickToTradeTraceModel(
        trace_id=to_optional_str(data.get("trace_id")) or "unknown",
        tick_receive_ts_ns=tick_recv,
        signal_ts_ns=sig_ts,
        gate_ts_ns=gate_ts,
        execution_ts_ns=exec_ts,
        tick_to_signal_us=to_optional_int(data.get("tick_to_signal_us")) or 0,
        signal_to_gate_us=to_optional_int(data.get("signal_to_gate_us")) or 0,
        gate_to_execution_us=to_optional_int(data.get("gate_to_execution_us")) or 0,
        total_tick_to_trade_us=total,
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_runtime_health(data: dict[str, Any]) -> RuntimeHealthModel | None:
    def _lane(prefix: str) -> LaneHealthModel:
        return LaneHealthModel(
            lane=data.get(f"{prefix}_lane", prefix),
            status=data.get(f"{prefix}_status", "unknown"),
            last_heartbeat_ts_ns=to_optional_int(data.get(f"{prefix}_heartbeat_ns")),
            age_ms=to_optional_int(data.get(f"{prefix}_age_ms")),
            stale=bool(data.get(f"{prefix}_stale", False)),
            missing=bool(data.get(f"{prefix}_missing", False)),
            reason_code=to_optional_str(data.get(f"{prefix}_reason")),
        )
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return RuntimeHealthModel(
        run_main_strategy_signal=_lane("main_strategy"),
        run_gate_engine=_lane("gate_engine"),
        run_execution_lane=_lane("execution_lane"),
        ai_lane_advisory=_lane("ai_advisory"),
        data_health=_lane("data"),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


# Parser dispatch: logical_name → (snapshot_field, parser_fn)
_PARSERS: dict[str, tuple[str, Any]] = {
    # Only streams that ND actually publishes
    "book_top": ("book_top", _parse_book_top),
    "book_l2": ("book_l2", _parse_book_l2),
    "account": ("account", _parse_account),
    "positions": ("positions", _parse_positions),
    "signal": ("latest_signal_preview", _parse_signal),
    "gate": ("latest_gate_decision", _parse_gate),
    "trade_action": ("latest_trade_action", _parse_trade_action),
    "execution": ("latest_execution_report", _parse_execution),
    "tick_to_trade": ("tick_to_trade", _parse_tick_to_trade),
}


def parse_stream_entry(logical_name: str, fields: dict[bytes, bytes]) -> tuple[str, Any] | None:
    """Parse a Redis stream entry into a (field_name, model) tuple."""
    if logical_name not in _PARSERS:
        return None
    field_name, parser = _PARSERS[logical_name]
    data = parse_stream_fields(fields)
    result = parser(data)
    if result is None:
        return None
    return field_name, result
