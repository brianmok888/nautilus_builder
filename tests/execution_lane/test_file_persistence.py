from __future__ import annotations

import json
from pathlib import Path

from packages.execution_lane.models import ExecutionLaneCommand, ExecutionLaneMode, ExecutionLaneProfile
from packages.execution_lane.persistence import ExecutionLaneFilePersistence


def _make_profile(runtime_profile_id: str = "rp_001") -> ExecutionLaneProfile:
    return ExecutionLaneProfile(
        tenant_id="tenant_001",
        project_id="project_001",
        runtime_profile_id=runtime_profile_id,
        profile_name="Test Profile",
        lane_mode=ExecutionLaneMode.PAPER,
        enabled=True,
        consumes_stream="exec_lane_events",
        adapter_id="BINANCE",
        venue="BINANCE",
        paper_trading_enabled=True,
    )


def _make_command(command_id: str = "cmd_001") -> ExecutionLaneCommand:
    return ExecutionLaneCommand(
        command_id=command_id,
        runtime_profile_id="rp_001",
        tenant_id="tenant_001",
        project_id="project_001",
        lane_mode=ExecutionLaneMode.PAPER,
        adapter_id="BINANCE",
        venue="BINANCE",
        strategy_lineage_id="sl_001",
        strategy_version_id="sv_001",
        trade_action_id="ta_001",
        source_event_id="se_001",
        idempotency_key="ik_001",
        order_intent={"instrument_id": "BTCUSDT-PERP.BINANCE"},
        risk_decision={"status": "approved"},
    )


def test_save_and_load_profile(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    profile = _make_profile()
    store.save_profile(profile)

    loaded = store.load_profile("rp_001")
    assert loaded is not None
    assert loaded.runtime_profile_id == "rp_001"
    assert loaded.adapter_id == "BINANCE"


def test_load_missing_profile_returns_none(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    assert store.load_profile("nonexistent") is None


def test_save_and_load_command(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    command = _make_command()
    store.save_command(command)

    loaded = store.load_command("cmd_001")
    assert loaded is not None
    assert loaded.strategy_lineage_id == "sl_001"


def test_list_profile_ids(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    for pid in ("rp_a", "rp_b", "rp_c"):
        store.save_profile(_make_profile(pid))
    assert store.list_profile_ids() == ["rp_a", "rp_b", "rp_c"]


def test_list_command_ids(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    for cid in ("cmd_x", "cmd_y"):
        store.save_command(_make_command(cid))
    assert store.list_command_ids() == ["cmd_x", "cmd_y"]


def test_persist_dir_respects_env(monkeypatch, tmp_path: Path) -> None:
    custom = tmp_path / "custom"
    monkeypatch.setenv("BUILDER_EXECUTION_LANE_PERSIST_DIR", str(custom))
    store = ExecutionLaneFilePersistence()
    assert store.base_dir == custom


def test_persisted_files_are_valid_json(tmp_path: Path) -> None:
    store = ExecutionLaneFilePersistence(base_dir=tmp_path)
    store.save_profile(_make_profile())
    store.save_command(_make_command())

    for path in tmp_path.glob("*.json"):
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
