from __future__ import annotations

import hashlib
import json
import math
import re
from enum import Enum
from statistics import mean, pstdev
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .engine_contract import NAUTILUS_TRADER_VERSION

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_RUN_ID_FIELDS = (
    "user_id",
    "project_id",
    "strategy_lineage_id",
    "strategy_version_id",
    "compile_hash",
    "validation_report_id",
    "dataset_id",
    "catalog_path",
    "source_mode",
    "dataset_source",
    "adapter_id",
    "instrument_id",
    "requested_data_type",
    "timeframe",
    "market_type",
    "date_range",
    "engine_mode",
)


class BacktestSourceMode(str, Enum):
    CATALOG = "catalog"
    LOCAL_FIXTURE = "local_fixture"
    EXTERNAL_MIRROR_MANIFEST = "external_mirror_manifest"
    USER_FETCHED_MANIFEST = "user_fetched_manifest"
    SYNTHETIC_TEST_KIT = "synthetic_test_kit"


class BacktestArtifactScope(str, Enum):
    PROJECT_ARTIFACT = "project_artifact"
    FIXTURE_DEV_ONLY = "fixture_dev_only"


class BacktestArtifactRef(BaseModel):
    """Scoped artifact pointer safe enough to include in Builder run manifests."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    scope: BacktestArtifactScope

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if _SAFE_NAME_RE.fullmatch(value) is None:
            raise ValueError("artifact name must be a safe identifier")
        return value

    @field_validator("checksum_sha256")
    @classmethod
    def validate_checksum(cls, value: str) -> str:
        if _SHA256_RE.fullmatch(value) is None:
            raise ValueError("checksum_sha256 must be a 64-character hex sha256 digest")
        return value.lower()

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, value: str) -> str:
        if "/" not in value:
            raise ValueError("media_type must be an IANA-style type/subtype")
        return value

    @model_validator(mode="after")
    def validate_uri_scope(self) -> "BacktestArtifactRef":
        if "\\" in self.uri or _has_traversal_segment(self.uri):
            raise ValueError("artifact URI must not contain traversal")
        if self.scope == BacktestArtifactScope.PROJECT_ARTIFACT and not self.uri.startswith("artifact://builder/"):
            raise ValueError("project artifacts must use artifact://builder URIs")
        if self.scope == BacktestArtifactScope.FIXTURE_DEV_ONLY and not self.uri.startswith("fixture://"):
            raise ValueError("fixture artifacts must use fixture:// URIs")
        return self


class BacktestDatasetProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    catalog_path: str = Field(min_length=1)
    source_mode: BacktestSourceMode
    dataset_source: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    requested_data_type: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    market_type: str = Field(min_length=1)
    date_range: str = Field(min_length=1)
    manifest_checksum_sha256: str | None = None
    manifest_file_count: int | None = Field(default=None, ge=0)

    @field_validator("manifest_checksum_sha256")
    @classmethod
    def validate_optional_checksum(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if _SHA256_RE.fullmatch(value) is None:
            raise ValueError("manifest_checksum_sha256 must be a 64-character hex sha256 digest")
        return value.lower()


class BacktestRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    compile_hash: str = Field(min_length=1)
    validation_report_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    catalog_path: str = Field(min_length=1)
    source_mode: BacktestSourceMode
    dataset_source: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    requested_data_type: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    market_type: str = Field(min_length=1)
    date_range: str = Field(min_length=1)
    engine_mode: str = Field(min_length=1)
    catalog_manifest_checksum_sha256: str | None = None
    catalog_manifest_file_count: int | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def populate_run_id(cls, data: object) -> object:
        if isinstance(data, dict) and not data.get("run_id"):
            candidate = dict(data)
            material = {field: candidate.get(field) for field in _RUN_ID_FIELDS}
            candidate["run_id"] = f"bt_run_{_sha256_hex(material)[:16]}"
            return candidate
        return data

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, value: str | None) -> str:
        if value is None or not value:
            raise ValueError("run_id is required")
        if _SAFE_NAME_RE.fullmatch(value) is None:
            raise ValueError("run_id must be a safe identifier")
        return value

    @field_validator("catalog_manifest_checksum_sha256")
    @classmethod
    def validate_optional_checksum(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if _SHA256_RE.fullmatch(value) is None:
            raise ValueError("catalog_manifest_checksum_sha256 must be a 64-character hex sha256 digest")
        return value.lower()

    def dataset_provenance(self) -> BacktestDatasetProvenance:
        return BacktestDatasetProvenance(
            dataset_id=self.dataset_id,
            catalog_path=self.catalog_path,
            source_mode=self.source_mode,
            dataset_source=self.dataset_source,
            adapter_id=self.adapter_id,
            instrument_id=self.instrument_id,
            requested_data_type=self.requested_data_type,
            timeframe=self.timeframe,
            market_type=self.market_type,
            date_range=self.date_range,
            manifest_checksum_sha256=self.catalog_manifest_checksum_sha256,
            manifest_file_count=self.catalog_manifest_file_count,
        )


class BacktestReportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: dict[str, float | int] = Field(default_factory=dict)
    sections: list[str] = Field(default_factory=list)
    chart_sections: list[str] = Field(default_factory=list)
    live_trading_enabled: Literal[False] = False
    execution_authority: Literal[False] = False


class BacktestRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    compile_hash: str = Field(min_length=1)
    validation_report_id: str = Field(min_length=1)
    dataset: BacktestDatasetProvenance
    engine_mode: str = Field(min_length=1)
    nautilus_trader_version: str = NAUTILUS_TRADER_VERSION
    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    artifacts: list[BacktestArtifactRef] = Field(default_factory=list)
    report_summary: BacktestReportSummary
    orders: int = Field(default=0, ge=0)
    positions: int = Field(default=0, ge=0)
    credentials_used: Literal[False] = False
    live_trading_enabled: Literal[False] = False
    execution_authority: Literal[False] = False
    manifest_checksum_sha256: str = ""

    @field_validator("manifest_checksum_sha256")
    @classmethod
    def validate_manifest_checksum(cls, value: str) -> str:
        if value == "":
            return value
        if _SHA256_RE.fullmatch(value) is None:
            raise ValueError("manifest_checksum_sha256 must be a 64-character hex sha256 digest")
        return value.lower()


def build_report_summary(raw_result: dict[str, object]) -> BacktestReportSummary:
    trades = _list_value(raw_result.get("trades"))
    fills = _list_value(raw_result.get("fills"))
    logs = _list_value(raw_result.get("logs"))
    equity_curve = _numeric_list(raw_result.get("equity_curve"))

    metrics: dict[str, float | int] = {
        "trade_count": len(trades),
        "fill_count": len(fills),
    }
    sections = ["summary"]
    chart_sections: list[str] = []

    if equity_curve:
        metrics["equity_points"] = len(equity_curve)
        if equity_curve[0] != 0:
            metrics["total_return"] = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        metrics["max_drawdown"] = _max_drawdown(equity_curve)
        returns = _returns(equity_curve)
        if returns:
            metrics["sharpe_ratio"] = _sharpe_ratio(returns)
        sections.append("equity_curve")
        chart_sections.extend(["equity_curve", "drawdown"])
    if trades:
        sections.append("trades")
    if fills:
        sections.append("fills")
    if logs:
        sections.append("logs")
    sections.append("artifacts")

    return BacktestReportSummary(
        metrics={key: _clean_number(value) for key, value in metrics.items()},
        sections=sections,
        chart_sections=chart_sections,
    )


def build_backtest_run_manifest(
    *,
    request: BacktestRunRequest,
    artifacts: list[BacktestArtifactRef],
    raw_result: dict[str, object],
    started_at: str,
    finished_at: str,
    worker_id: str,
) -> BacktestRunManifest:
    manifest = BacktestRunManifest(
        run_id=request.run_id,
        user_id=request.user_id,
        project_id=request.project_id,
        strategy_lineage_id=request.strategy_lineage_id,
        strategy_version_id=request.strategy_version_id,
        compile_hash=request.compile_hash,
        validation_report_id=request.validation_report_id,
        dataset=request.dataset_provenance(),
        engine_mode=request.engine_mode,
        started_at=started_at,
        finished_at=finished_at,
        worker_id=worker_id,
        artifacts=artifacts,
        report_summary=build_report_summary(raw_result),
        orders=_int_value(raw_result.get("orders")),
        positions=_int_value(raw_result.get("positions")),
    )
    payload = manifest.model_dump(mode="json")
    payload["manifest_checksum_sha256"] = ""
    checksum = _sha256_hex(payload)
    return manifest.model_copy(update={"manifest_checksum_sha256": checksum})


def _has_traversal_segment(uri: str) -> bool:
    return any(segment == ".." for segment in uri.replace("\\", "/").split("/"))


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _numeric_list(value: object) -> list[float]:
    if not isinstance(value, list):
        return []
    result: list[float] = []
    for item in value:
        try:
            number = float(item)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result.append(number)
    return result


def _returns(values: list[float]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(values, values[1:]):
        if previous != 0:
            returns.append((current - previous) / previous)
    return returns


def _max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        if peak != 0:
            max_drawdown = min(max_drawdown, (value - peak) / peak)
    return max_drawdown


def _sharpe_ratio(returns: list[float]) -> float:
    if not returns:
        return 0.0
    deviation = pstdev(returns)
    if deviation == 0:
        return 0.0
    return mean(returns) / deviation * math.sqrt(len(returns))


def _int_value(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _clean_number(value: float | int) -> float | int:
    if isinstance(value, int):
        return value
    if not math.isfinite(value):
        return 0.0
    return float(value)
