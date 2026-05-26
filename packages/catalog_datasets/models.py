from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from packages.auth import ScopedArtifactRef

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_FIXTURE_SOURCE_MODES = {"local_fixture", "synthetic_test_kit"}
_MANIFEST_SOURCE_MODES = {"external_mirror_manifest", "user_fetched_manifest"}


class CatalogSourceMode(str, Enum):
    CATALOG = "catalog"
    LOCAL_FIXTURE = "local_fixture"
    EXTERNAL_MIRROR_MANIFEST = "external_mirror_manifest"
    USER_FETCHED_MANIFEST = "user_fetched_manifest"
    SYNTHETIC_TEST_KIT = "synthetic_test_kit"


class CatalogCacheMode(str, Enum):
    READ_ONLY = "read_only"
    REFRESHABLE_MANIFEST = "refreshable_manifest"
    FIXTURE = "fixture"


class CatalogDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    market_type: str = Field(min_length=1)
    date_range: str = Field(min_length=1)
    catalog_path: str = Field(min_length=1)
    source: str = "user_selected_catalog"
    source_mode: CatalogSourceMode = CatalogSourceMode.CATALOG
    cache_mode: CatalogCacheMode = CatalogCacheMode.READ_ONLY
    manifest_ref: str | None = None
    cache_key: str | None = None

    @model_validator(mode="before")
    @classmethod
    def default_cache_key(cls, data: object) -> object:
        if isinstance(data, dict) and not data.get("cache_key") and data.get("dataset_id"):
            candidate = dict(data)
            candidate["cache_key"] = str(candidate["dataset_id"])
            return candidate
        return data

    @field_validator("catalog_path")
    @classmethod
    def normalize_catalog_path(cls, value: str) -> str:
        return Path(value).expanduser().as_posix()

    @field_validator("cache_key")
    @classmethod
    def validate_cache_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if _SAFE_IDENTIFIER.fullmatch(value) is None:
            raise ValueError("cache_key must be a safe identifier")
        return value

    @field_validator("manifest_ref")
    @classmethod
    def validate_manifest_ref_shape(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if ".." in value.replace("\\", "/").split("/"):
            raise ValueError("manifest_ref must not contain traversal")
        return value

    @model_validator(mode="after")
    def validate_source_policy(self) -> "CatalogDataset":
        source_mode = self.source_mode.value
        cache_mode = self.cache_mode.value
        if source_mode in _MANIFEST_SOURCE_MODES:
            if not self.manifest_ref:
                raise ValueError("manifest_ref is required for manifest-backed dataset source modes")
            if not self.manifest_ref.startswith("artifact://builder/"):
                raise ValueError("manifest_ref must be a Builder artifact")
            if cache_mode != CatalogCacheMode.REFRESHABLE_MANIFEST.value:
                raise ValueError("manifest source modes require refreshable_manifest cache mode")
        if source_mode in _FIXTURE_SOURCE_MODES and cache_mode != CatalogCacheMode.FIXTURE.value:
            raise ValueError("fixture source modes require fixture cache mode")
        return self

    @property
    def scoped_artifact(self) -> ScopedArtifactRef:
        return ScopedArtifactRef(
            artifact_type="CatalogDataset",
            artifact_id=self.dataset_id,
            user_id=self.user_id,
            project_id=self.project_id,
        )
