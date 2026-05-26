from __future__ import annotations

import pytest

from packages.execution_lane import ExecutionLaneService


def test_credential_slot_writes_local_env_and_returns_redacted_slot(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)

    slot = service.create_credential_slot(
        {
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
        }
    )

    env_file = tmp_path / ".env.execution.local"
    assert env_file.exists()
    assert "BINANCE_API_KEY=test-binance-key" in env_file.read_text(encoding="utf-8")
    assert "BINANCE_API_SECRET=test-binance-secret" in env_file.read_text(encoding="utf-8")
    assert slot.credential_slot_ref.startswith("credslot://local-env/")
    assert slot.env_file_path == ".env.execution.local"
    assert slot.secrets_storage == "local_env_file"
    assert slot.browser_secret_echo is False
    assert slot.redacted_keys == ["BINANCE_API_KEY", "BINANCE_API_SECRET"]
    assert "test-binance" not in slot.model_dump_json()
    assert len(slot.fingerprint) == 64


def test_credential_slot_rejects_public_or_unsafe_env_names(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)

    bad_payload = {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_paper_tradingnode",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "lane_mode": "paper",
        "requested_by": "ops_user",
        "credential_values": {"NEXT_PUBLIC_BINANCE_API_KEY": "leak-me"},
    }
    with pytest.raises(ValueError, match="unsafe credential env key"):
        service.create_credential_slot(bad_payload)

    traversal_payload = {**bad_payload, "credential_values": {"../BINANCE_API_SECRET": "leak-me"}}
    with pytest.raises(ValueError, match="unsafe credential env key"):
        service.create_credential_slot(traversal_payload)

    generic_payload = {**bad_payload, "credential_values": {"API_KEY": "too-generic"}}
    with pytest.raises(ValueError, match="venue-prefixed"):
        service.create_credential_slot(generic_payload)


def test_profile_can_reference_created_slot_without_raw_credentials(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    slot = service.create_credential_slot(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {"BINANCE_API_KEY": "test-binance-key"},
        }
    )

    profile = service.register_profile(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "profile_name": "Paper TradingNode lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "credential_slot_ref": slot.credential_slot_ref,
            "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
        }
    )
    plan = service.build_trading_node_runtime_plan(runtime_profile_id=profile.runtime_profile_id)

    assert profile.credential_slot_ref == slot.credential_slot_ref
    assert plan.readiness_status == "READY"
    assert plan.credential_slot_ref == slot.credential_slot_ref
    assert plan.may_submit_order is False
    assert plan.config_contract["data_clients"]["BINANCE"]["credential_slot_ref"] == slot.credential_slot_ref
    assert "test-binance-key" not in str(plan.model_dump(mode="json"))


def test_profile_rejects_unknown_or_cross_scope_credential_slot(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)

    with pytest.raises(ValueError, match="credential slot is not registered"):
        service.register_profile(
            {
                "tenant_id": "tenant_a",
                "project_id": "project_alpha",
                "runtime_profile_id": "rp_paper_tradingnode",
                "profile_name": "Paper TradingNode lane",
                "lane_mode": "paper",
                "enabled": True,
                "paper_trading_enabled": True,
                "adapter_id": "BINANCE_PERP",
                "venue": "BINANCE",
                "credential_slot_ref": "credslot://local-env/unknown",
                "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
            }
        )
