from __future__ import annotations

import inspect
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION
from services.api.dev_server import BuilderApiHandler
import services.workers.execution_lane_worker as execution_lane_worker


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_exposes_headless_backend_entrypoints() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    scripts = pyproject["project"]["scripts"]

    assert scripts["nautilus-builder-api"] == "services.api.dev_server:main"
    assert scripts["nautilus-builder-execution-worker"] == "services.workers.execution_lane_worker:main"
    assert scripts["nautilus-builder-backend-check"] == "services.backend_runtime:main"


def test_headless_runtime_report_proves_backend_without_web_or_daedalus() -> None:
    from packages.backend_runtime import verify_headless_backend_runtime

    report = verify_headless_backend_runtime(runtime_profile_id="rp_paper_001")
    payload = report.model_dump(mode="json")

    assert payload["mode"] == "headless_backend"
    assert payload["web_ui_required"] is False
    assert payload["nautilus_daedalus_required"] is False
    assert payload["dependency_free_api"]["health"]["status"] == "ok"
    assert payload["dependency_free_api"]["adapters_count"] > 0
    if payload["fastapi_app"]["mounted"]:
        assert payload["fastapi_app"]["route_count"] >= 30
    else:
        assert "fastapi" in str(payload["fastapi_app"]["error"]).lower()
    assert payload["execution_lane"]["runtime_profile_id"] == "rp_paper_001"
    assert payload["execution_lane"]["strategy_lane_coupled"] is False
    assert payload["execution_lane"]["may_submit_order"] is False
    assert payload["execution_lane"]["ui_features"]["credential_inputs_allowed"] is False
    assert payload["nautilus_trader"]["expected_version"] == NAUTILUS_TRADER_VERSION
    assert payload["nautilus_trader"]["is_match"] is True
    assert payload["no_web_imports"] is True
    assert payload["no_daedalus_imports"] is True


def test_fastapi_app_factory_mounts_under_project_uv_environment() -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from services.api.fastapi_app import create_fastapi_app; app=create_fastapi_app(); print(app.title, len(app.routes))",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Nautilus Builder API" in result.stdout
    assert int(result.stdout.strip().rsplit(" ", 1)[-1]) >= 30


def test_dependency_free_dev_server_app_serves_json_contract_without_web_imports() -> None:
    health = BuilderApiHandler.app.get("/health")
    adapters = BuilderApiHandler.app.get("/api/adapters")

    assert health.status_code == 200
    assert health.json()["service"] == "nautilus_builder_api"
    assert adapters.status_code == 200
    assert adapters.json()
    assert "apps.web" not in sys.modules


def test_execution_lane_worker_stays_standalone_and_strategy_decoupled() -> None:
    source = inspect.getsource(execution_lane_worker)

    assert "strategy_lane_coupled" in source
    assert "strategy_spec" not in source
    assert "strategy_registry" not in source
    assert "nautilus_rule_graph" not in source
    assert "submit_order" not in source
    assert "TradeAction" not in source


def test_backend_runtime_cli_prints_headless_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.backend_runtime",
            "--runtime-profile-id",
            "rp_paper_001",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "headless_backend"
    assert payload["web_ui_required"] is False
    assert payload["execution_lane"]["strategy_lane_coupled"] is False
    assert payload["execution_lane"]["may_submit_order"] is False
    assert payload["nautilus_trader"]["expected_version"] == NAUTILUS_TRADER_VERSION
