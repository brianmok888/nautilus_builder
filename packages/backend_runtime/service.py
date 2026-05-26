from __future__ import annotations

import sys
from typing import Iterable

from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
from packages.execution_lane import ExecutionLaneService
from services.api.app import create_app

from .models import (
    DependencyFreeApiReport,
    FastApiAppReport,
    HeadlessBackendRuntimeReport,
    NautilusRuntimeReport,
    RuntimeEntrypoint,
)

DAEDALUS_MODULE_PREFIXES = (
    "nautilus_actors",
    "nautilus_adapters",
    "nautilus_brain",
    "nautilus_runtime",
    "nautilus_strategies",
    "nautilus_dinger",
)
WEB_MODULE_PREFIXES = ("apps.web",)

HEADLESS_ENTRYPOINTS: tuple[RuntimeEntrypoint, ...] = (
    RuntimeEntrypoint(
        name="dependency_free_api",
        kind="http_api",
        target="services.api.dev_server:main",
        command="python3 -m services.api.dev_server --host 127.0.0.1 --port 8000",
    ),
    RuntimeEntrypoint(
        name="fastapi_api",
        kind="http_api",
        target="services.api.fastapi_app:create_fastapi_app",
        command="uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory --host 0.0.0.0 --port 8000",
    ),
    RuntimeEntrypoint(
        name="execution_lane_worker",
        kind="worker",
        target="services.workers.execution_lane_worker:main",
        command="python3 -m services.workers.execution_lane_worker --runtime-profile-id rp_paper_001",
    ),
    RuntimeEntrypoint(
        name="backend_check",
        kind="diagnostic",
        target="services.backend_runtime:main",
        command="python3 -m services.backend_runtime --runtime-profile-id rp_paper_001",
    ),
)


def verify_headless_backend_runtime(*, runtime_profile_id: str = "rp_paper_001") -> HeadlessBackendRuntimeReport:
    """Return executable evidence that Builder backend seams run without web/ND coupling."""
    dependency_free_api = _dependency_free_api_report()
    fastapi_report = _fastapi_app_report()
    execution_lane = ExecutionLaneService().snapshot(runtime_profile_id=runtime_profile_id)
    runtime_status = check_nautilus_runtime_version()
    loaded_web_modules = _loaded_modules_with_prefixes(WEB_MODULE_PREFIXES)
    loaded_daedalus_modules = _loaded_modules_with_prefixes(DAEDALUS_MODULE_PREFIXES)

    return HeadlessBackendRuntimeReport(
        entrypoints=list(HEADLESS_ENTRYPOINTS),
        dependency_free_api=dependency_free_api,
        fastapi_app=fastapi_report,
        execution_lane=execution_lane,
        nautilus_trader=NautilusRuntimeReport(
            package_name=runtime_status.package_name,
            expected_version=runtime_status.expected_version,
            installed_version=runtime_status.installed_version,
            is_match=runtime_status.is_match,
            message=runtime_status.message,
        ),
        no_web_imports=not loaded_web_modules,
        no_daedalus_imports=not loaded_daedalus_modules,
        loaded_web_modules=loaded_web_modules,
        loaded_daedalus_modules=loaded_daedalus_modules,
    )


def _dependency_free_api_report() -> DependencyFreeApiReport:
    app = create_app()
    health_response = app.get("/health")
    adapters_response = app.get("/api/adapters")
    adapters_payload = adapters_response.json()
    adapters_count = len(adapters_payload) if isinstance(adapters_payload, list) else 0
    return DependencyFreeApiReport(
        health=health_response.json(),
        adapters_count=adapters_count,
        routes_count=len(getattr(app, "routes", getattr(app, "_routes", {}))),
    )


def _fastapi_app_report() -> FastApiAppReport:
    try:
        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app()
    except Exception as exc:  # pragma: no cover - exercised only when optional runtime deps are absent
        return FastApiAppReport(mounted=False, route_count=0, error=str(exc))
    return FastApiAppReport(
        mounted=True,
        title=getattr(app, "title", None),
        version=getattr(app, "version", None),
        route_count=len(getattr(app, "routes", [])),
    )


def _loaded_modules_with_prefixes(prefixes: Iterable[str]) -> list[str]:
    ordered_prefixes = tuple(prefixes)
    return sorted(
        name
        for name in sys.modules
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in ordered_prefixes)
    )
