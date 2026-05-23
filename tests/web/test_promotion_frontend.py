from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_promotion_panel_exposes_shadow_only_request_and_manual_approval() -> None:
    panel = (ROOT / "apps" / "web" / "components" / "promotions" / "PromotionRequestPanel.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "requestShadowPromotion" in api
    assert "shadow" in panel
    assert "signal-preview" in panel
    assert "manual approval" in panel
    assert "strategy_version_id" in panel
    assert "result_id" in panel
    assert "submit_order" not in panel
    assert "TradeAction" not in panel
