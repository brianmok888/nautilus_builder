"""H1: Builder must track Daedalus's nautilus_trader version within 2 minor releases."""
from __future__ import annotations

import tomllib
from pathlib import Path


def test_nautilus_trader_version_is_aligned_with_daedalus() -> None:
    pyproject = Path("pyproject.toml").read_text()
    deps = tomllib.loads(pyproject).get("project", {}).get("dependencies", [])
    nt_dep = [d for d in deps if "nautilus_trader" in d]
    assert len(nt_dep) == 1, f"expected exactly 1 nautilus_trader dep, got: {nt_dep}"
    dep = nt_dep[0]
    assert "1.227.0" in dep, f"nautilus_trader must be 1.227.0, got: {dep}"


def test_imported_nautilus_version_matches_pinned() -> None:
    import nautilus_trader
    version = getattr(nautilus_trader, "__version__", "")
    assert version.startswith("1.227"), f"installed nautilus_trader version: {version}"
