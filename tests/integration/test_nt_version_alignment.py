"""H1: Builder must track Daedalus's nautilus_trader version within 2 minor releases.

The expected version is derived from the single source of truth
(`packages/backtest_runner/engine_contract.NAUTILUS_TRADER_VERSION`), which mirrors
the pinned `pyproject.toml` dependency, so this test never silently drifts when
the pin is bumped.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION


def test_nautilus_trader_version_is_aligned_with_daedalus() -> None:
    pyproject = Path("pyproject.toml").read_text()
    deps = tomllib.loads(pyproject).get("project", {}).get("dependencies", [])
    nt_dep = [d for d in deps if "nautilus_trader" in d]
    assert len(nt_dep) == 1, f"expected exactly 1 nautilus_trader dep, got: {nt_dep}"
    dep = nt_dep[0]
    expected = f"nautilus_trader=={NAUTILUS_TRADER_VERSION}"
    assert dep == expected, (
        f"nautilus_trader must be pinned to {expected} (matches "
        f"engine_contract + Daedalus alignment), got: {dep}"
    )


def test_imported_nautilus_version_matches_pinned() -> None:
    import nautilus_trader

    version = getattr(nautilus_trader, "__version__", "")
    assert version == NAUTILUS_TRADER_VERSION, (
        f"installed nautilus_trader version {version} does not match the pinned "
        f"runtime version {NAUTILUS_TRADER_VERSION}"
    )
