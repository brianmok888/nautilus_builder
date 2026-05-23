from __future__ import annotations

from services.api.app import create_app


def test_promotion_request_api_accepts_shadow_only_stable_ids() -> None:
    response = create_app().post(
        "/api/promotions/request",
        json={"strategy_version_id": "strategy_001_v002", "result_id": "res_001", "target": "shadow"},
    )

    assert response.status_code == 201
    assert response.json()["target"] == "shadow"
    assert response.json()["manual_approval_required"] is True


def test_promotion_request_api_rejects_live_targets() -> None:
    response = create_app().post(
        "/api/promotions/request",
        json={"strategy_version_id": "strategy_001_v002", "result_id": "res_001", "target": "live"},
    )

    assert response.status_code == 422
