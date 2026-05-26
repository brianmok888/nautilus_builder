from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimeEntrypoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    target: str = Field(min_length=1)
    command: str = Field(min_length=1)
    requires_web_ui: bool = False
    requires_nautilus_daedalus: bool = False


class NautilusRuntimeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(min_length=1)
    expected_version: str = Field(min_length=1)
    installed_version: str | None
    is_match: bool
    message: str = Field(min_length=1)


class DependencyFreeApiReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health: dict[str, Any]
    adapters_count: int = Field(ge=0)
    routes_count: int = Field(ge=0)


class FastApiAppReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mounted: bool
    title: str | None = None
    version: str | None = None
    route_count: int = Field(ge=0)
    error: str | None = None


class HeadlessBackendRuntimeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = "headless_backend"
    web_ui_required: bool = False
    nautilus_daedalus_required: bool = False
    entrypoints: list[RuntimeEntrypoint]
    dependency_free_api: DependencyFreeApiReport
    fastapi_app: FastApiAppReport
    execution_lane: dict[str, Any]
    nautilus_trader: NautilusRuntimeReport
    no_web_imports: bool
    no_daedalus_imports: bool
    loaded_web_modules: list[str]
    loaded_daedalus_modules: list[str]
