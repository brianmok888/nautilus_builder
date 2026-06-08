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


def test_frontend_visual_shell_uses_approved_ant_design_stack() -> None:
    package = json.loads((WEB / "package.json").read_text())
    css = (WEB / "app" / "globals.css").read_text()

    assert "antd" in package.get("dependencies", {})
    assert "@ant-design/icons" in package.get("dependencies", {})
    assert "vue" not in package.get("dependencies", {})
    assert "@ant-design-vue/pro-layout" not in package.get("dependencies", {})
    assert "tailwindcss" not in package.get("dependencies", {})
    assert "tailwindcss" not in package.get("devDependencies", {})
    assert "@mui/material" not in package.get("dependencies", {})
    assert "@chakra-ui/react" not in package.get("dependencies", {})
    assert "no live order authority" in css
    assert ".operator-shell" in css
    assert ".builder-dashboard" in css


def test_next_config_does_not_freeze_api_proxy_rewrites_at_build_time() -> None:
    config = (WEB / "next.config.mjs").read_text()
    middleware = (WEB / "middleware.ts").read_text()

    assert "outputFileTracingRoot" in config
    assert "async rewrites" not in config
    assert "BUILDER_API_BASE_URL" not in config
    assert "NEXT_PUBLIC_API_BASE_URL" not in config
    assert "/api/:path*" not in config
    assert "/health/backend" not in config
    assert 'const API_PREFIX = "/api/"' in middleware
    assert 'const HEALTH_BACKEND_PATH = "/health/backend"' in middleware
    assert "process.env.BUILDER_API_BASE_URL" in middleware
