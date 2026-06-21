"""Deterministic mock data generator for TradeHUD contracts.

Uses seeded PRNG for reproducibility. All data is synthetic/mock provenance.
No exchange credentials. No live data.
"""

from __future__ import annotations

import time
from typing import Any

from packages.tradehud_contracts.models import (
    SourceFreshnessMeta,
    MarketBookTopModel,
    MarketBookL2Model,
    BookLevelModel,
    StrategySignalPreviewModel,
    GateDecisionModel,
    TradeActionEvidenceModel,
    ExecutionReportModel,
    AccountSnapshotModel,
    PositionSnapshotModel,
    OpenOrderSnapshotModel,
    AssetSnapshotModel,
    QuantLevelModel,
    QuantLevelsContextModel,
    TickToTradeTraceModel,
    LaneHealthModel,
    RuntimeHealthModel,
    TradeHudSnapshot,
)

VENUE = "BINANCE-FUTURES"
ACCOUNT_ID = "acc_paper_001"


class SeededRng:
    """Deterministic LCG PRNG — no Math.random equivalent."""

    def __init__(self, seed: int = 42) -> None:
        self._state = seed & 0xFFFFFFFF

    def next(self) -> float:
        self._state = (1664525 * self._state + 1013904223) & 0xFFFFFFFF
        return self._state / 0x100000000

    def range(self, lo: float, hi: float) -> float:
        return lo + self.next() * (hi - lo)

    def randint(self, lo: int, hi: int) -> int:
        return int(self.range(lo, hi + 1))

    def choice(self, items: list[Any]) -> Any:
        return items[self.randint(0, len(items) - 1)]


def _now_ns() -> int:
    return int(time.time() * 1_000_000_000)


def _hash_stub(prefix: str, n: int) -> str:
    h = format((n * 2654435761) & 0xFFFFFFFF, "08x")
    return f"{prefix}_{h}{h}{h}{h}"


def _fresh(ts_ns: int | None, provenance: str = "mock") -> dict[str, Any]:
    """Build freshness meta dict for model construction."""
    if ts_ns is None:
        return SourceFreshnessMeta(
            source_available=False,
            stale=True,
            missing=True,
            provenance=provenance,
            source_status="missing",
        ).model_dump()
    return SourceFreshnessMeta(
        source_available=True,
        last_update_ts_ns=ts_ns,
        receive_ts_ns=ts_ns,
        age_ms=0,
        stale=False,
        missing=False,
        provenance=provenance,
        source_status="synthetic",
    ).model_dump()


SYMBOL_PROFILES = {
    "BTCUSDT-PERP": {"base_price": 105_000.0, "tick_size": 0.1},
    "ETHUSDT-PERP": {"base_price": 3_800.0, "tick_size": 0.01},
}


def generate_snapshot(symbol: str = "BTCUSDT-PERP", seed: int = 42) -> TradeHudSnapshot:
    """Generate a complete deterministic TradeHUD snapshot."""
    rng = SeededRng(seed)
    profile = SYMBOL_PROFILES.get(symbol, SYMBOL_PROFILES["BTCUSDT-PERP"])
    price = profile["base_price"]
    ts = _now_ns()

    # Book top
    spread = profile["tick_size"] * rng.range(1, 5)
    bid = price - spread / 2
    ask = price + spread / 2
    mid = (bid + ask) / 2
    bid_size = rng.range(0.5, 20)
    ask_size = rng.range(0.5, 20)
    book_top = MarketBookTopModel(
        symbol=symbol,
        bid_price=bid,
        ask_price=ask,
        bid_size=bid_size,
        ask_size=ask_size,
        mid_price=mid,
        spread=spread,
        spread_bps=(spread / mid) * 10_000,
        microprice=mid + (ask_size - bid_size) / (ask_size + bid_size) * spread * 0.5,
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Book L2
    bids: list[BookLevelModel] = []
    asks: list[BookLevelModel] = []
    bid_total = 0.0
    ask_total = 0.0
    for i in range(15):
        bp = bid - i * profile["tick_size"] * rng.range(1, 5)
        bs = rng.range(0.1, 30) * (1 - i * 0.05)
        bid_total += bs
        bids.append(BookLevelModel(price=bp, size=bs, total=bid_total, age_ms=rng.randint(0, 3000)))

        ap = ask + i * profile["tick_size"] * rng.range(1, 5)
        a_s = rng.range(0.1, 30) * (1 - i * 0.05)
        ask_total += a_s
        asks.append(BookLevelModel(price=ap, size=a_s, total=ask_total, age_ms=rng.randint(0, 3000)))
    top5_bid = sum(level.size for level in bids[:5])
    top5_ask = sum(level.size for level in asks[:5])
    book_l2 = MarketBookL2Model(
        symbol=symbol,
        bids=bids,
        asks=asks,
        spread=spread,
        spread_bps=(spread / mid) * 10_000,
        microprice=book_top.microprice,
        top5_imbalance=top5_bid / (top5_bid + top5_ask),
        checksum=_hash_stub("ck", seed),
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Signal preview
    direction = rng.choice(["long", "short", "flat"])
    signal = StrategySignalPreviewModel(
        signal_id=f"sig_{seed}",
        symbol=symbol,
        feature_hash=_hash_stub("feat", seed),
        context_hash=_hash_stub("ctx", seed),
        policy_hash=_hash_stub("pol", seed),
        graph_trace_hash=_hash_stub("gtr", seed),
        confidence_score=rng.range(0.3, 0.85),
        direction=direction,
        target_hint=price * 1.01 if direction == "long" else price * 0.99 if direction == "short" else None,
        invalidation_hint=price * 0.995 if direction == "long" else price * 1.005,
        size_hint=rng.range(0.1, 2.0) if direction != "flat" else None,
        preview_note="Preview only — NOT EXECUTABLE",
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Gate decisions — one of each type
    gate_approved = GateDecisionModel(
        decision_id=f"gate_{seed}_approved",
        decision="APPROVED",
        reason_code="all_gates_passed",
        confidence_delta=rng.range(0, 0.15),
        size_modifier=rng.range(0.5, 1.0),
        target_hint=price * 1.005,
        invalidation_hint=price * 0.995,
        gate_decision_hash=_hash_stub("gd", seed * 7),
        source_signal_hash=_hash_stub("sig", seed * 3),
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Trade action (evidence only)
    trade_action = TradeActionEvidenceModel(
        action_id=f"ta_{seed}",
        action="PLACE_LIMIT",
        side="buy",
        price=price,
        qty=rng.range(0.05, 1.0),
        trade_action_hash=_hash_stub("ta", seed * 11),
        source_gate_decision_hash=gate_approved.gate_decision_hash,
        created_by="run_gate_engine",
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Execution report
    submit_ts = ts - rng.randint(100_000, 5_000_000)
    ack_ts = submit_ts + rng.randint(50_000, 500_000)
    fill_ts = ack_ts + rng.randint(100_000, 2_000_000)
    exec_report = ExecutionReportModel(
        report_id=f"exec_{seed}",
        status="FILLED",
        exchange_order_id=f"BIN-{rng.randint(100000000, 999999999)}",
        client_order_id=f"CO-{seed}",
        trade_action_hash=trade_action.trade_action_hash,
        symbol=symbol,
        side="buy",
        filled_qty=rng.range(0.05, 1.0),
        avg_fill_price=price,
        submit_ts_ns=submit_ts,
        ack_ts_ns=ack_ts,
        fill_ts_ns=fill_ts,
        submit_to_ack_us=(ack_ts - submit_ts) // 1000,
        ack_to_fill_us=(fill_ts - ack_ts) // 1000,
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Account
    unrealized = rng.range(-5_000, 8_000)
    account = AccountSnapshotModel(
        account_id=ACCOUNT_ID,
        venue=VENUE,
        balance=250_000.0,
        equity=250_000.0 + unrealized,
        available_margin=175_000.0,
        margin_used=rng.range(5_000, 50_000),
        unrealized_pnl=unrealized,
        realized_pnl=rng.range(-2_000, 15_000),
        ts_event_ns=ts,
        **_fresh(ts),
    )

    # Positions
    positions = [
        PositionSnapshotModel(
            symbol=symbol, venue=VENUE,
            side="long", qty=rng.range(0.1, 3.0),
            entry_price=price - rng.range(-200, 200),
            mark_price=price,
            unrealized_pnl=rng.range(-3_000, 5_000),
            realized_pnl=rng.range(-500, 2_000),
            margin=rng.range(5_000, 30_000),
            ts_event_ns=ts, **_fresh(ts),
        ),
    ]
    if symbol != "ETHUSDT-PERP":
        positions.append(PositionSnapshotModel(
            symbol="ETHUSDT-PERP", venue=VENUE,
            side="short", qty=rng.range(1, 20),
            entry_price=3800.0, mark_price=3800.0 + rng.range(-30, 30),
            unrealized_pnl=rng.range(-800, 1_200),
            realized_pnl=0.0,
            margin=rng.range(2_000, 10_000),
            ts_event_ns=ts, **_fresh(ts),
        ))

    # Open orders
    open_orders = []
    for i in range(rng.randint(0, 4)):
        open_orders.append(OpenOrderSnapshotModel(
            order_id=f"O-{seed}-{i}",
            client_order_id=f"CO-{seed}-{i}",
            symbol=symbol, venue=VENUE,
            side=rng.choice(["buy", "sell"]),
            order_type=rng.choice(["LIMIT", "STOP", "STOP_LIMIT"]),
            price=price + rng.range(-100, 100),
            qty=rng.range(0.05, 1.5),
            filled_qty=0, status="LIVE",
            ts_event_ns=ts, **_fresh(ts),
        ))

    # Assets
    assets = [
        AssetSnapshotModel(asset="USDT", free=250_000.0, locked=30_000.0, usd_value=250_000.0, ts_event_ns=ts, **_fresh(ts)),
        AssetSnapshotModel(asset="BTC", free=0.5, locked=0.1, usd_value=52_500.0, ts_event_ns=ts, **_fresh(ts)),
        AssetSnapshotModel(asset="ETH", free=15.0, locked=0.0, usd_value=57_000.0, ts_event_ns=ts, **_fresh(ts)),
    ]

    # Quant levels
    quant_levels = QuantLevelsContextModel(
        symbol=symbol,
        levels=[
            QuantLevelModel(label="R2", price=price * 1.02, kind="resistance"),
            QuantLevelModel(label="R1", price=price * 1.01, kind="resistance"),
            QuantLevelModel(label="Pivot", price=price, kind="pivot"),
            QuantLevelModel(label="S1", price=price * 0.99, kind="support"),
            QuantLevelModel(label="S2", price=price * 0.98, kind="support"),
        ],
        ts_event_ns=ts, **_fresh(ts),
    )

    # Tick-to-trade
    t2s = rng.range(50, 500)
    s2g = rng.range(100, 800)
    g2e = rng.range(200, 1500)
    tick_to_trade = TickToTradeTraceModel(
        trace_id=f"trc_{seed}",
        tick_receive_ts_ns=ts - int(t2s + s2g + g2e) * 1000,
        signal_ts_ns=ts - int(s2g + g2e) * 1000,
        gate_ts_ns=ts - int(g2e) * 1000,
        execution_ts_ns=ts,
        tick_to_signal_us=int(t2s),
        signal_to_gate_us=int(s2g),
        gate_to_execution_us=int(g2e),
        total_tick_to_trade_us=int(t2s + s2g + g2e),
        ts_event_ns=ts, **_fresh(ts),
    )

    # Runtime health
    def mk_lane(lane: str, healthy: bool) -> LaneHealthModel:
        return LaneHealthModel(
            lane=lane,
            status="healthy" if healthy else "stale",
            last_heartbeat_ts_ns=ts if healthy else ts - rng.randint(10_000_000_000, 30_000_000_000),
            age_ms=rng.randint(0, 2000) if healthy else rng.randint(10_000, 30_000),
            stale=not healthy,
            missing=False,
            reason_code=None if healthy else "HEARTBEAT_TIMEOUT",
        )
    runtime_health = RuntimeHealthModel(
        run_main_strategy_signal=mk_lane("run_main_strategy_signal", True),
        run_gate_engine=mk_lane("run_gate_engine", True),
        run_execution_lane=mk_lane("run_execution_lane", True),
        ai_lane_advisory=mk_lane("ai_lane_advisory", True),
        data_health=mk_lane("data_health", True),
        ts_event_ns=ts, **_fresh(ts),
    )

    return TradeHudSnapshot(
        book_top=book_top,
        book_l2=book_l2,
        latest_signal_preview=signal,
        latest_gate_decision=gate_approved,
        latest_trade_action=trade_action,
        latest_execution_report=exec_report,
        account=account,
        positions=positions,
        open_orders=open_orders,
        assets=assets,
        quant_levels=quant_levels,
        tick_to_trade=tick_to_trade,
        runtime_health=runtime_health,
        provenance="mock",
    )
