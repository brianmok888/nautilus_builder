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
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# --- LOCAL DEVELOPMENT ONLY safety guards -------------------------------------
# This tool writes synthetic ND TradeHUD contract fixtures into Redis Streams.
# It must NEVER be used in production or pointed at non-local trading
# infrastructure. These guards enforce that at runtime, not just in comments.

_LOCAL_REDIS_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", ""})
_PRODUCTION_ENV_VALUES = frozenset({"production", "prod", "staging", "stage"})
_PRODUCTION_ENV_VARS = ("BUILDER_ENV", "APP_ENV", "ENVIRONMENT")


def is_local_redis_host(redis_url: str) -> bool:
    """True iff the Redis URL points at an explicitly local host.

    Allowed hosts: ``localhost``, ``127.0.0.1``, ``::1``, or no host (which the
    redis client resolves to localhost). Any other hostname/IP is non-local.
    """
    if not redis_url:
        return True
    try:
        parsed = urlparse(redis_url)
    except (ValueError, TypeError):
        return False
    host = (parsed.hostname or "").lower()
    # IPv6 literal hosts may arrive bracketed; urlparse already strips brackets.
    host = host.strip("[]")
    return host in _LOCAL_REDIS_HOSTS


def redact_redis_url(redis_url: str) -> str:
    """Return a Redis URL with any userinfo (password) removed for safe logging.

    The host/port/db are preserved so operators retain connection context while
    secrets (passwords/tokens embedded as userinfo) are never logged.
    """
    if not redis_url:
        return redis_url or ""
    try:
        parsed = urlparse(redis_url)
    except (ValueError, TypeError):
        return "<redacted: unparseable redis url>"
    # Rebuild the URL WITHOUT netloc userinfo. Keep scheme/host/port/path only.
    netloc = parsed.hostname or ""
    if netloc:
        # Preserve IPv6 bracketing for readability.
        if ":" in netloc and not netloc.startswith("["):
            netloc = f"[{netloc}]"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
    return f"{parsed.scheme}://{netloc}{parsed.path}"


def is_production_like_env(environ: dict[str, str] | None = None) -> bool:
    """True iff any production-like environment variable is set."""
    env = environ if environ is not None else os.environ
    for var in _PRODUCTION_ENV_VARS:
        val = (env.get(var, "") or "").strip().lower()
        if val in _PRODUCTION_ENV_VALUES:
            return True
    return False


def validate_local_dev_guard(
    redis_url: str,
    *,
    allow_nonlocal: bool = False,
    environ: dict[str, str] | None = None,
) -> None:
    """Enforce LOCAL DEVELOPMENT ONLY constraints at runtime.

    Raises ``SystemExit`` (non-zero) when:
      * any production-like environment is active (BUILDER_ENV / APP_ENV /
        ENVIRONMENT in production/prod/staging/stage), regardless of host or
        override; OR
      * the Redis URL points at a non-local host and the operator did NOT pass
        the explicit scary ``--allow-nonlocal-redis-for-fixture-replay`` flag.

    The override bypasses the HOST allowlist ONLY; it can never bypass the
    production-environment guard.
    """
    if is_production_like_env(environ):
        logger.error(
            "Refusing to run TradeHUD fixture replay: a production-like "
            "environment is active (BUILDER_ENV/APP_ENV/ENVIRONMENT). This tool "
            "is LOCAL DEVELOPMENT ONLY and must never touch production Redis."
        )
        raise SystemExit(2)

    if not is_local_redis_host(redis_url) and not allow_nonlocal:
        logger.error(
            "Refusing to run TradeHUD fixture replay: Redis URL host is "
            "non-local (%s). This tool is LOCAL DEVELOPMENT ONLY. To target a "
            "non-local Redis deliberately (still forbidden in production), pass "
            "--allow-nonlocal-redis-for-fixture-replay.",
            redact_redis_url(redis_url),
        )
        raise SystemExit(2)


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
    parser.add_argument(
        "--allow-nonlocal-redis-for-fixture-replay",
        action="store_true",
        default=False,
        help=(
            "DANGER: bypass the local-Redis host allowlist. This tool is LOCAL "
            "DEVELOPMENT ONLY and must NEVER be pointed at production trading "
            "infrastructure. This flag overrides the HOST check ONLY; it cannot "
            "override the production-environment guard (BUILDER_ENV/APP_ENV/"
            "ENVIRONMENT=production/prod/staging/stage always exits)."
        ),
    )
    args = parser.parse_args()

    fixture_dir = Path(args.fixture_dir)
    if not fixture_dir.exists():
        logger.error("Fixture directory not found: %s", fixture_dir)
        sys.exit(1)

    # LOCAL DEVELOPMENT ONLY runtime guard: reject production envs and non-local
    # Redis hosts unless the scary override flag is explicitly passed.
    validate_local_dev_guard(
        args.redis_url,
        allow_nonlocal=args.allow_nonlocal_redis_for_fixture_replay,
    )

    logger.info("=== TradeHUD ND Fixture Replay (LOCAL DEV ONLY) ===")
    # Never log the raw Redis URL: it may embed a password/token.
    logger.info("Redis URL: %s", redact_redis_url(args.redis_url))
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
