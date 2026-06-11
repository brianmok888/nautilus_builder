"""Feature registry — canonical list of known ND microstructure features."""
from __future__ import annotations

# Canonical feature names grouped by domain
BOOK_FEATURES = {
    "book.best_bid", "book.best_ask", "book.spread_bps", "book.mid_price",
    "book.obi", "book.depth_top_n_usd", "book.depth_near_mid_usd",
    "book.wall_bid_usd", "book.wall_ask_usd", "book.wall_persistence_ms",
    "book.pull_stack_score", "book.resilience_score",
}

TRADES_FEATURES = {
    "trades.aggressor_buy_volume", "trades.aggressor_sell_volume",
    "trades.delta", "trades.delta_rate", "trades.cvd",
    "trades.trade_count", "trades.burst_score", "trades.absorption_score",
    "trades.footprint_imbalance",
}

SVP_FEATURES = {
    "svp.poc", "svp.vah", "svp.val", "svp.hvn_nearest",
    "svp.lvn_nearest", "svp.distance_to_poc_bps",
}

FUNDING_FEATURES = {
    "funding.rate", "funding.predicted_rate", "funding.basis",
    "funding.zscore", "funding.regime",
}

LIQUIDATION_FEATURES = {
    "liquidation.long_liq_notional", "liquidation.short_liq_notional",
    "liquidation.imbalance", "liquidation.event_count",
    "liquidation.largest_event_notional", "liquidation.cluster_score",
    "liquidation.cascade_risk",
}

VWAP_FEATURES = {
    "vwap.session", "vwap.session_distance_bps", "vwap.session_zscore",
    "vwap.anchored", "vwap.anchored_distance_bps",
}

SOURCE_FEATURES = {
    "source.book_age_ms", "source.trades_age_ms", "source.funding_age_ms",
    "source.liquidation_age_ms", "source.book_stale", "source.trades_stale",
    "source.missing", "source.synthetic_fallback_used",
    "source.true_zero", "source.available",
}

ALL_KNOWN_FEATURES = (
    BOOK_FEATURES | TRADES_FEATURES | SVP_FEATURES | FUNDING_FEATURES
    | LIQUIDATION_FEATURES | VWAP_FEATURES | SOURCE_FEATURES
)

# Classic indicators (v1-compatible)
CLASSIC_INDICATORS = {
    "ema", "sma", "rsi", "macd", "atr", "bollinger", "vwap",
}


def is_known_feature(feature_name: str) -> bool:
    """Check if a feature name is recognized."""
    return feature_name in ALL_KNOWN_FEATURES or feature_name.lower() in CLASSIC_INDICATORS


def is_microstructure_feature(feature_name: str) -> bool:
    """Check if a feature requires microstructure data sources."""
    return feature_name in (BOOK_FEATURES | TRADES_FEATURES | LIQUIDATION_FEATURES | SVP_FEATURES)
