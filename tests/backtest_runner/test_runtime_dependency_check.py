from __future__ import annotations

import importlib.metadata

import pytest

from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION
from packages.backtest_runner.runtime_check import (
    assert_nautilus_runtime_version,
    check_nautilus_runtime_version,
)


def test_runtime_dependency_check_rejects_version_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda package: "0.0.0")

    status = check_nautilus_runtime_version()

    assert status.expected_version == NAUTILUS_TRADER_VERSION
    assert status.installed_version == "0.0.0"
    assert status.is_match is False
    assert "expected nautilus_trader" in status.message


def test_runtime_dependency_check_accepts_pinned_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda package: NAUTILUS_TRADER_VERSION)

    status = check_nautilus_runtime_version()

    assert status.installed_version == NAUTILUS_TRADER_VERSION
    assert status.is_match is True
    assert assert_nautilus_runtime_version().is_match is True


def test_active_python_environment_uses_pinned_nautilus_runtime() -> None:
    status = check_nautilus_runtime_version()

    assert status.installed_version == NAUTILUS_TRADER_VERSION
    assert status.is_match is True, status.message
