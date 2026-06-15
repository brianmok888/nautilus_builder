"""TradeHUD ND fixture replay tool — LOCAL DEVELOPMENT ONLY.

Replays deterministic ND TradeHUD contract fixtures into Redis Streams.
Does not connect to exchanges.
Does not submit, cancel, modify, or approve orders.
Does not create production TradeAction authority.

Usage:
    python scripts/tradehud_replay_nd_fixtures.py \
        --redis-url redis://127.0.0.1:6379/0 \
        --fixture-dir tests/fixtures/tradehud_nd_contracts \
        --namespace nd \
        --interval-ms 500

SAFETY:
    This script uses XADD to write fixtures to Redis for local development.
    It must NEVER be used in production or connected to live trading infrastructure.
    Only run_execution_lane may call submit_order() in Nautilus-Daedalus runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Fixture filename → nd.* stream key mapping
FIXTURE_TO_STREAM = {
    "nd_market_book_top.jsonl": "nd.market.book_top",
    "nd_market_book_l2.jsonl": "nd.market.book_l2",
    "nd_market_trades.jsonl": "nd.market.trades",
    "nd_strategy_signal_preview.jsonl": "nd.strategy_signal_preview",
    "nd_gate_decision.jsonl": "nd.gate_decision",
    "nd_trade_action.jsonl": "nd.trade_action",
    "nd_execution_report.jsonl": "nd.execution_report",
    "nd_health.jsonl": "nd.health",
    "nd_quant_levels_context.jsonl": "nd.quant_levels.context",
    "nd_tick_to_trade_trace.jsonl": "nd.tick_to_trade.trace",
    "nd_account_snapshot.jsonl": "nd.account.snapshot",
    "nd_position_snapshot.jsonl": "nd.position.snapshot",
    "nd_order_snapshot.jsonl": "nd.order.snapshot",
    "nd_order_event.jsonl": "nd.order.event",
}


def load_fixture_records(fixture_dir: Path) -> dict[str, list[dict]]:
    """Load all fixture files and map to stream keys."""
    result: dict[str, list[dict]] = {}
    for fname, stream_key in FIXTURE_TO_STREAM.items():
        fpath = fixture_dir / fname
        if not fpath.exists():
            logger.warning("Skipping missing fixture: %s", fname)
            continue
        records = []
        for line in fpath.read_text().strip().split("\n"):
            if line.strip():
                records.append(json.loads(line))
        result[stream_key] = records
        logger.info("Loaded %d records for %s", len(records), stream_key)
    return result


def build_stream_name(stream_key: str, namespace: str) -> str:
    """Build actual Redis stream name from namespace."""
    if namespace == "nd":
        return stream_key
    # Legacy: nautilus:tradehud:<suffix>
    suffix = stream_key.split(".")[-1]
    return f"nautilus:tradehud:{suffix}"


async def replay_fixtures(
    redis_url: str,
    fixture_dir: Path,
    namespace: str,
    interval_ms: int,
    loop: bool,
) -> None:
    """Replay fixture records into Redis streams."""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.error("redis package not installed. Install: pip install redis")
        sys.exit(1)

    client = aioredis.from_url(redis_url)
    await client.ping()
    logger.info("Connected to Redis: %s", redis_url)

    fixtures = load_fixture_records(fixture_dir)
    if not fixtures:
        logger.error("No fixtures loaded from %s", fixture_dir)
        return

    round_num = 0
    while True:
        round_num += 1
        logger.info("=== Replay round %d ===", round_num)

        for stream_key, records in fixtures.items():
            redis_stream = build_stream_name(stream_key, namespace)
            for record in records:
                # Serialize all values as strings for Redis
                fields = {}
                for k, v in record.items():
                    if isinstance(v, (dict, list)):
                        fields[k] = json.dumps(v)
                    elif isinstance(v, bool):
                        fields[k] = str(v).lower()
                    else:
                        fields[k] = str(v)
                await client.xadd(redis_stream, fields)
                logger.debug("XADD %s: %s", redis_stream, record.get("event_type", stream_key))
                await asyncio.sleep(interval_ms / 1000.0)

        if not loop:
            logger.info("Replay complete (single pass).")
            break

        logger.info("Loop mode: waiting %dms before next round...", interval_ms)
        await asyncio.sleep(interval_ms / 1000.0)

    await client.aclose()
    logger.info("Redis connection closed.")


def main():
    parser = argparse.ArgumentParser(
        description="Replay ND TradeHUD fixtures into Redis Streams (LOCAL DEV ONLY)"
    )
    parser.add_argument(
        "--redis-url", required=True,
        help="Redis URL, e.g. redis://127.0.0.1:6379/0",
    )
    parser.add_argument(
        "--fixture-dir", default="tests/fixtures/tradehud_nd_contracts",
        help="Directory containing ND fixture JSONL files",
    )
    parser.add_argument(
        "--namespace", default="nd", choices=["nd", "nautilus_tradehud"],
        help="Stream namespace (default: nd)",
    )
    parser.add_argument(
        "--interval-ms", type=int, default=500,
        help="Delay between records in milliseconds (default: 500)",
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Loop continuously instead of single pass",
    )
    args = parser.parse_args()

    fixture_dir = Path(args.fixture_dir)
    if not fixture_dir.exists():
        logger.error("Fixture directory not found: %s", fixture_dir)
        sys.exit(1)

    logger.info("=== TradeHUD ND Fixture Replay (LOCAL DEV ONLY) ===")
    logger.info("Redis URL: %s", args.redis_url)
    logger.info("Fixture dir: %s", fixture_dir)
    logger.info("Namespace: %s", args.namespace)
    logger.info("Interval: %dms", args.interval_ms)
    logger.info("Loop: %s", args.loop)

    asyncio.run(replay_fixtures(
        redis_url=args.redis_url,
        fixture_dir=fixture_dir,
        namespace=args.namespace,
        interval_ms=args.interval_ms,
        loop=args.loop,
    ))


if __name__ == "__main__":
    main()
