from __future__ import annotations

from packages.execution_lane import ExecutionLaneService
from services.api.app import create_app


def test_execution_lane_credential_slot_route_writes_redacted_local_env(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    app = create_app(execution_lane_service=service)

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
    assert response.status_code == 201
    assert payload["credential_slot_ref"].startswith("credslot://local-env/")
    assert payload["redacted_keys"] == ["BINANCE_API_KEY", "BINANCE_API_SECRET"]
    assert payload["browser_secret_echo"] is False
    assert payload["env_file_path"] == ".env.execution.local"
    assert "test-binance" not in str(payload)
    assert "BINANCE_API_KEY=test-binance-key" in (tmp_path / ".env.execution.local").read_text(encoding="utf-8")


def test_execution_lane_credential_slot_route_rejects_unsafe_env_key(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    app = create_app(execution_lane_service=service)

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

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_execution_lane_credential_slot"
    assert "unsafe credential env key" in response.json()["details"]
