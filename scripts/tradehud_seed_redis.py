"""TradeHUD Redis seeder — LOCAL DEVELOPMENT ONLY.

Seeds deterministic TradeHUD Redis Stream events for local UI testing.
Does not connect to exchanges.
Does not submit, cancel, modify, or approve orders.
Does not create production TradeAction authority.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import random
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Default streams to seed
DEFAULT_STREAMS = [
    "nd.market.book_top",
    "nd.market.book_l2",
    "nd.market.trades",
    "nd.strategy_signal_preview",
    "nd.gate_decision",
    "nd.trade_action",
    "nd.execution_report",
    "nd.health",
    "nd.account.snapshot",
    "nd.position.snapshot",
    "nd.order.snapshot",
]

# Simulated base prices per symbol
BASE_PRICES = {
    "BTCUSDT-PERP": 67000.0,
    "ETHUSDT-PERP": 3500.0,
}

TRADE_SIDES = ["BUY", "SELL"]
TRADE_AGGRESSORS = ["BUY", "SELL", "MAKER"]


def _ts_ns() -> int:
    return int(time.time() * 1_000_000_000)


def _build_book_top(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    spread = base * 0.0002
    mid = base + math.sin(tick * 0.01) * spread * 2
    bid = mid - spread / 2
    ask = mid + spread / 2
    return {
        "symbol": symbol,
        "bid_price": f"{bid:.1f}",
        "ask_price": f"{ask:.1f}",
        "bid_size": f"{random.uniform(0.1, 5.0):.4f}",
        "ask_size": f"{random.uniform(0.1, 5.0):.4f}",
        "mid_price": f"{mid:.1f}",
        "spread": f"{spread:.1f}",
        "spread_bps": f"{spread/mid*10000:.1f}",
        "microprice": f"{(bid*ask) / (bid+ask):.1f}",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_book_l2(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    bids = []
    asks = []
    for i in range(10):
        bid_price = base - (i + 1) * base * 0.0001
        ask_price = base + (i + 1) * base * 0.0001
        bids.append({"price": f"{bid_price:.1f}", "size": f"{random.uniform(0.01, 3.0):.4f}", "total": "0", "age_ms": str(i * 100)})
        asks.append({"price": f"{ask_price:.1f}", "size": f"{random.uniform(0.01, 3.0):.4f}", "total": "0", "age_ms": str(i * 100)})
    return {
        "symbol": symbol,
        "bids": json.dumps(bids),
        "asks": json.dumps(asks),
        "spread": f"{abs(asks[0]['price'] - bids[0]['price']):.1f}",
        "spread_bps": "2.0",
        "microprice": f"{BASE_PRICES.get(symbol, 50000):.1f}",
        "top5_imbalance": f"{random.uniform(-0.3, 0.3):.4f}",
        "checksum": f"seed_{tick}",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_trade(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    side = random.choice(TRADE_SIDES)
    price = base + random.uniform(-base * 0.001, base * 0.001)
    qty = random.uniform(0.001, 2.0)
    flags = []
    if random.random() < 0.05:
        flags.append("large_trade")
    if random.random() < 0.02:
        flags.append("sweep")
    is_liq = random.random() < 0.01
    if is_liq:
        flags.append("long_liq" if side == "SELL" else "short_liq")
    return {
        "symbol": symbol,
        "price": f"{price:.1f}",
        "qty": f"{qty:.4f}",
        "notional": f"{price * qty:.2f}",
        "side": side,
        "aggressor": random.choice(TRADE_AGGRESSORS),
        "trade_id": f"seed_{_ts_ns()}_{tick}",
        "flags": ",".join(flags) if flags else "",
        "source": "seeded_mock",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_signal(symbol: str, tick: int) -> dict:
    return {
        "symbol": symbol,
        "signal_id": f"sig_seed_{tick}",
        "feature_hash": f"fhash_{tick}",
        "context_hash": f"chash_{tick}",
        "policy_hash": f"phash_{tick}",
        "graph_trace_hash": f"ghash_{tick}",
        "confidence_score": f"{random.uniform(0.3, 0.9):.3f}",
        "direction": random.choice(["long", "short", "flat"]),
        "target_hint": f"{BASE_PRICES.get(symbol, 50000) * 1.01:.1f}",
        "invalidation_hint": f"{BASE_PRICES.get(symbol, 50000) * 0.99:.1f}",
        "size_hint": f"{random.uniform(0.01, 0.5):.4f}",
        "preview_note": "Preview only — NOT EXECUTABLE",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_gate(symbol: str, tick: int) -> dict:
    decision = random.choices(["APPROVED", "HOLD", "REJECTED"], weights=[0.3, 0.6, 0.1])[0]
    return {
        "symbol": symbol,
        "decision_id": f"gate_seed_{tick}",
        "decision": decision,
        "first_blocking_gate": "max_position" if decision == "REJECTED" else None,
        "reason_code": "ok" if decision == "APPROVED" else ("hold" if decision == "HOLD" else "max_position"),
        "confidence_delta": f"{random.uniform(-0.1, 0.1):.3f}",
        "size_modifier": "1.0",
        "target_hint": None,
        "invalidation_hint": None,
        "gate_decision_hash": f"gdec_{tick}",
        "source_signal_hash": f"sig_{tick}",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_trade_action(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    return {
        "symbol": symbol,
        "action_id": f"ta_seed_{tick}",
        "action": "BUY",
        "side": "buy",
        "price": f"{base + random.uniform(-10, 10):.1f}",
        "qty": f"{random.uniform(0.01, 0.1):.4f}",
        "trade_action_hash": f"tahash_{tick}",
        "source_gate_decision_hash": f"gdec_{tick}",
        "created_by": "run_gate_engine",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_execution(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    submit_ts = _ts_ns() - random.randint(1000, 50000)
    return {
        "symbol": symbol,
        "report_id": f"exec_seed_{tick}",
        "status": "FILLED",
        "exchange_order_id": f"exch_{tick}",
        "client_order_id": f"client_{tick}",
        "trade_action_hash": f"tahash_{tick}",
        "side": "buy",
        "filled_qty": f"{random.uniform(0.01, 0.1):.4f}",
        "avg_fill_price": f"{base:.1f}",
        "submit_ts_ns": str(submit_ts),
        "ack_ts_ns": str(submit_ts + random.randint(100, 5000)),
        "fill_ts_ns": str(submit_ts + random.randint(500, 50000)),
        "submit_to_ack_us": str(random.randint(100, 5000)),
        "ack_to_fill_us": str(random.randint(500, 50000)),
        "ts_event_ns": str(_ts_ns()),
    }


def _build_health(tick: int) -> dict:
    lanes = ["main_strategy", "gate_engine", "execution_lane", "ai_advisory", "data"]
    fields = {}
    for lane in lanes:
        healthy = random.random() > 0.05
        fields[f"{lane}_lane"] = lane
        fields[f"{lane}_status"] = "healthy" if healthy else "degraded"
        fields[f"{lane}_heartbeat_ns"] = str(_ts_ns() - random.randint(0, 2000000000))
        fields[f"{lane}_age_ms"] = str(random.randint(10, 500))
        fields[f"{lane}_stale"] = "False"
        fields[f"{lane}_missing"] = "False"
        fields[f"{lane}_reason"] = ""
    fields["ts_event_ns"] = str(_ts_ns())
    return fields


def _build_account(symbol: str, tick: int) -> dict:
    return {
        "account_id": "acc_seed_001",
        "venue": "BINANCE-FUTURES",
        "balance": f"{100000.0 + math.sin(tick * 0.05) * 5000:.2f}",
        "equity": f"{105000.0 + math.sin(tick * 0.05) * 5000:.2f}",
        "available_margin": f"{95000.0 + math.sin(tick * 0.05) * 5000:.2f}",
        "margin_used": f"{5000.0:.2f}",
        "unrealized_pnl": f"{math.sin(tick * 0.1) * 2000:.2f}",
        "realized_pnl": f"{tick * 10:.2f}",
        "currency": "USDT",
        "ts_event_ns": str(_ts_ns()),
    }


def _build_position(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    side = random.choice(["long", "short", "flat"])
    qty = random.uniform(0.01, 0.5) if side != "flat" else 0.0
    return {
        "positions": json.dumps([{
            "symbol": symbol,
            "venue": "BINANCE-FUTURES",
            "side": side,
            "qty": f"{qty:.4f}",
            "entry_price": f"{base:.1f}",
            "mark_price": f"{base + math.sin(tick * 0.01) * 100:.1f}",
            "unrealized_pnl": f"{math.sin(tick * 0.01) * 500:.2f}",
            "realized_pnl": "0.0",
            "margin": f"{base * qty * 0.1:.2f}",
            "ts_event_ns": str(_ts_ns()),
        }]),
    }


def _build_order(symbol: str, tick: int) -> dict:
    base = BASE_PRICES.get(symbol, 50000.0)
    return {
        "orders": json.dumps([{
            "order_id": f"ord_seed_{tick}",
            "client_order_id": f"cord_{tick}",
            "symbol": symbol,
            "venue": "BINANCE-FUTURES",
            "side": random.choice(["buy", "sell"]),
            "order_type": "LIMIT",
            "price": f"{base + random.uniform(-100, 100):.1f}",
            "qty": f"{random.uniform(0.01, 0.1):.4f}",
            "filled_qty": "0.0",
            "status": "LIVE",
            "ts_event_ns": str(_ts_ns()),
        }]),
    }


_STREAM_BUILDERS = {
    "nd.market.book_top": lambda sym, tick: _build_book_top(sym, tick),
    "nd.market.book_l2": lambda sym, tick: _build_book_l2(sym, tick),
    "nd.market.trades": lambda sym, tick: _build_trade(sym, tick),
    "nd.strategy_signal_preview": lambda sym, tick: _build_signal(sym, tick),
    "nd.gate_decision": lambda sym, tick: _build_gate(sym, tick),
    "nd.trade_action": lambda sym, tick: _build_trade_action(sym, tick),
    "nd.execution_report": lambda sym, tick: _build_execution(sym, tick),
    "nd.health": lambda sym, tick: _build_health(tick),
    "nd.account.snapshot": lambda sym, tick: _build_account(sym, tick),
    "nd.position.snapshot": lambda sym, tick: _build_position(sym, tick),
    "nd.order.snapshot": lambda sym, tick: _build_order(sym, tick),
}


async def seed_loop(redis_url: str, namespace: str, symbols: list[str], interval_ms: int) -> None:
    """Main seeding loop."""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.error("redis package not installed. pip install redis")
        sys.exit(1)

    client = aioredis.from_url(redis_url, decode_responses=False)
    try:
        await client.ping()
    except Exception as e:
        logger.error("Cannot connect to Redis: %s", e)
        sys.exit(1)

    # Map stream names
    stream_map = _STREAM_BUILDERS.copy()
    if namespace != "nd":
        # Remap to use the namespace prefix
        stream_map = {s.replace("nd.", f"{namespace}."): fn for s, fn in _STREAM_BUILDERS.items()}

    tick = 0
    logger.info("Seeding %d streams for %s at %dms interval", len(stream_map), symbols, interval_ms)
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            for symbol in symbols:
                for stream_key, builder in stream_map.items():
                    if stream_key == "nd.health":
                        data = builder(symbol, tick)
                    else:
                        data = builder(symbol, tick)
                    # Add provenance markers
                    data["provenance"] = "seeded_mock"
                    data["source_status"] = "synthetic"
                    try:
                        await client.xadd(stream_key, data)
                    except Exception as e:
                        logger.warning("XADD failed for %s: %s", stream_key, e)
            tick += 1
            logger.info("Seeded tick %d", tick)
            await asyncio.sleep(interval_ms / 1000)
    except KeyboardInterrupt:
        logger.info("Seeder stopped after %d ticks", tick)
    finally:
        await client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description="LOCAL DEVELOPMENT ONLY — TradeHUD Redis seeder")
    parser.add_argument("--redis-url", default="redis://127.0.0.1:6379/0", help="Redis URL")
    parser.add_argument("--namespace", default="nd", help="Stream namespace (nd, nautilus_tradehud, custom)")
    parser.add_argument("--symbols", nargs="+", default=["BTCUSDT-PERP", "ETHUSDT-PERP"], help="Symbols to seed")
    parser.add_argument("--interval-ms", type=int, default=1000, help="Interval between seed ticks in ms")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  LOCAL DEVELOPMENT ONLY                                     ║")
    print("║  This seeder does NOT connect to exchanges.                  ║")
    print("║  This seeder does NOT submit, cancel, or approve orders.    ║")
    print("║  All events: provenance=seeded_mock, source_status=synthetic║")
    print("╚══════════════════════════════════════════════════════════════╝")

    asyncio.run(seed_loop(args.redis_url, args.namespace, args.symbols, args.interval_ms))


if __name__ == "__main__":
    main()
