from __future__ import annotations

import importlib.metadata

import pytest

from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version


def test_exact_match_has_no_minor_drift() -> None:
    status = check_nautilus_runtime_version()
    assert status.installed_version == NAUTILUS_TRADER_VERSION
    assert status.is_match is True
    assert status.is_minor_drift is False


def test_minor_version_drift_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda pkg: "1.229.0")
    status = check_nautilus_runtime_version()
    assert status.is_match is False
    assert status.is_minor_drift is True
    assert "VERSION DRIFT" in status.message


def test_patch_only_drift_is_not_minor_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda pkg: "1.228.5")
    status = check_nautilus_runtime_version()
    assert status.is_match is False
    assert status.is_minor_drift is False
    assert "PATCH DRIFT" in status.message


def test_major_version_drift_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda pkg: "2.0.0")
    status = check_nautilus_runtime_version()
    assert status.is_match is False
    assert status.is_minor_drift is True
