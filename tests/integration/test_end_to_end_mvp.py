from __future__ import annotations

from packages.system_verification.e2e import run_mvp_verification


def test_visual_builder_to_strategy_spec_flow() -> None:
    report = run_mvp_verification()

    assert report.builder_to_spec is True
    assert report.ai_advisory_only is True


def test_api_worker_and_reconnect_flow() -> None:
    report = run_mvp_verification()

    assert report.runtime_persists_disconnect is True
    assert report.replay_endpoint_ok is True
    assert report.worker_integration_ok is True


def test_shadow_promotion_boundary_is_preserved() -> None:
    report = run_mvp_verification()

    assert report.builder_can_submit_orders is False
    assert report.promotion_signal_preview_only is True
    assert report.naming_consistency_ok is True
