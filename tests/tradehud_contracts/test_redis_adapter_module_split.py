"""Module-split invariants for the TradeHUD Redis adapter (P2-3 split).

Locks two contracts so the split cannot silently regress:
1. Public API symbols remain importable from packages.tradehud_contracts.redis_adapter.
2. The adapter module stays small (connection/IO only); parsing lives in
   redis_normalizers and snapshot assembly in redis_snapshot_builder.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import packages.tradehud_contracts.redis_adapter as adapter_mod


_PUBLIC_SYMBOLS = (
    "RedisStreamAdapter",
    "parse_stream_entry",
    "build_snapshot_from_redis",
)


@pytest.mark.parametrize("symbol", _PUBLIC_SYMBOLS)
def test_public_symbols_remain_importable_from_redis_adapter(symbol: str) -> None:
    """Backward compatibility: the public parse/snapshot/adapter symbols must stay
    importable from the original redis_adapter path after the P2-3 split."""
    assert hasattr(adapter_mod, symbol), (
        f"redis_adapter no longer re-exports {symbol}; the P2-3 split broke a "
        "public import contract."
    )


def test_internal_parse_helpers_remain_reachable_from_redis_adapter() -> None:
    """Tests and tooling historically reach into the `_parse_*` helpers via the
    redis_adapter namespace; the split must keep these reachable."""
    for name in (
        "_parse_book_top",
        "_parse_book_l2",
        "_parse_trade",
        "_parse_account",
        "_ns",
    ):
        assert hasattr(adapter_mod, name), f"redis_adapter lost re-export of {name}"


def test_redis_adapter_module_is_split_into_normalizers_and_snapshot() -> None:
    """The adapter must delegate parsing/normalization and snapshot assembly to
    dedicated modules rather than inlining them."""
    import packages.tradehud_contracts.redis_normalizers as normalizers
    import packages.tradehud_contracts.redis_snapshot_builder as snapshot

    assert hasattr(normalizers, "parse_stream_entry")
    assert hasattr(normalizers, "_PARSERS")
    assert hasattr(snapshot, "build_snapshot_from_redis")


def test_redis_adapter_module_stays_under_size_boundary() -> None:
    """redis_adapter.py must stay a thin connection/IO module (well under its
    pre-split 843 LOC). Parsing lives in redis_normalizers.py. Prevents a future
    regression that re-monolithizes the adapter."""
    root = Path(__file__).resolve().parents[2]
    adapter_loc = _count_loc(root / "packages" / "tradehud_contracts" / "redis_adapter.py")
    # Generous ceiling above the post-split ~260 LOC; the point is to catch a
    # re-monolithization, not to forbid modest additions.
    assert adapter_loc <= 400, (
        f"redis_adapter.py grew to {adapter_loc} LOC; parsing/normalization must "
        "live in redis_normalizers.py, not the adapter."
    )


def test_redis_normalizers_module_is_the_parse_home() -> None:
    """All `_parse_*` helpers must live in redis_normalizers (the parse home), not
    be re-defined in the adapter. Guards against duplication after the split."""
    root = Path(__file__).resolve().parents[2]
    adapter_src = (root / "packages" / "tradehud_contracts" / "redis_adapter.py").read_text()
    # The adapter must not DEFINE these (it may only re-export them).
    assert "\ndef _parse_book_top(" not in adapter_src
    assert "\ndef _parse_trade(" not in adapter_src
    assert "\ndef _parse_quant_levels(" not in adapter_src


def _count_loc(path: Path) -> int:
    lines = path.read_text().splitlines()
    return sum(1 for ln in lines if ln.strip() and not ln.strip().startswith("#"))
