from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def test_frontend_infrastructure_declares_lockfile_tsconfig_and_proxy() -> None:
    package = json.loads((WEB / "package.json").read_text())

    assert (WEB / "package-lock.json").exists()
    assert (WEB / "tsconfig.json").exists()
    assert (WEB / "next.config.mjs").exists()
    assert package["scripts"]["typecheck"] == "tsc --noEmit"
    assert package["scripts"]["test"].startswith("vitest run")


def test_typed_frontend_api_client_has_backend_base_health_and_errors() -> None:
    api = (WEB / "lib" / "api.ts").read_text()
    types = (WEB / "lib" / "types.ts").read_text()

    assert "ApiError" in api
    assert "apiFetch" in api
    assert "fetchBackendHealth" in api
    assert "NEXT_PUBLIC_API_BASE_URL" in api
    assert "StrategySummary" in types
    assert "BacktestProfileValidation" in types
    assert "strategy_lineage_id" in types


def test_frontend_test_runner_uses_esm_vitest_config_to_avoid_vite_cjs_warning() -> None:
    package = json.loads((WEB / "package.json").read_text())

    assert (WEB / "vitest.config.mts").exists()
    assert not (WEB / "vitest.config.ts").exists()
    assert "--config vitest.config.mts" in package["scripts"]["test"]


def test_playwright_webserver_unsets_color_env_conflict() -> None:
    config = (WEB / "playwright.config.ts").read_text()

    assert "unset FORCE_COLOR NO_COLOR" in config
