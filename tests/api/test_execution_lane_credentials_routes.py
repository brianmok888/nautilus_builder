from __future__ import annotations

from services.api.app import create_app


def test_execution_lane_credential_slot_route_rejects_browser_secret_bootstrap(tmp_path) -> None:
    app = create_app()

    response = app.post(
        "/api/execution-lane/credential-slots",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {
                "BINANCE_API_KEY": "test-binance-key",
                "BINANCE_API_SECRET": "test-binance-secret",
            },
        },
    )

    payload = response.json()
    assert response.status_code == 410
    assert payload["error"] == "credential_slot_http_disabled"
    assert "backend-only secret provisioning" in payload["details"]
    assert "test-binance" not in str(payload)
    assert not (tmp_path / ".env.execution.local").exists()


def test_execution_lane_credential_slot_route_does_not_validate_or_echo_browser_secret_values(tmp_path) -> None:
    app = create_app()

    response = app.post(
        "/api/execution-lane/credential-slots",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {"NEXT_PUBLIC_BINANCE_API_KEY": "must-not-leak"},
        },
    )

    assert response.status_code == 410
    assert response.json()["error"] == "credential_slot_http_disabled"
    assert "must-not-leak" not in str(response.json())
    assert not (tmp_path / ".env.execution.local").exists()
