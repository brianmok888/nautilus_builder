from __future__ import annotations

from pathlib import Path


def test_readme_limitations_reflect_current_package_api_and_frontend_reality() -> None:
    readme = Path("README.md").read_text()

    assert "pyproject.toml" in readme
    assert "uv.lock" in readme
    assert "services/api/fastapi_app.py" in readme
    assert "services/api/dev_server.py" in readme
    assert "Next.js app shell" in readme
    assert "no package manifest" not in readme
    assert "no committed Python lockfile" not in readme
    assert "no real API server bootstrap" not in readme
    assert "no real frontend app shell" not in readme


def test_readme_describes_catalog_backed_replay_without_production_overclaim() -> None:
    readme = Path("README.md").read_text()

    assert "catalog-backed Nautilus replay smoke" in readme
    assert "synthetic historical quote ticks" in readme
    assert "not a production-scale StrategySpec-generated replay" in readme
    assert "minimal BacktestEngine lifecycle smoke, not a full data/strategy replay" not in readme


def test_readme_mentions_new_production_readiness_closure_boundaries() -> None:
    readme = Path("README.md").read_text()

    assert "local JSON artifact store" in readme
    assert "tenant-scoped catalog dataset" in readme
    assert "StrategySpec-generated catalog replay" in readme
    assert "real auth middleware" in readme
