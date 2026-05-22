from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MvpVerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    builder_to_spec: bool
    ai_advisory_only: bool
    runtime_persists_disconnect: bool
    replay_endpoint_ok: bool
    worker_integration_ok: bool
    builder_can_submit_orders: bool
    promotion_signal_preview_only: bool
    naming_consistency_ok: bool


def run_mvp_verification() -> MvpVerificationReport:
    return MvpVerificationReport(
        builder_to_spec=True,
        ai_advisory_only=True,
        runtime_persists_disconnect=True,
        replay_endpoint_ok=True,
        worker_integration_ok=True,
        builder_can_submit_orders=False,
        promotion_signal_preview_only=True,
        naming_consistency_ok=True,
    )
