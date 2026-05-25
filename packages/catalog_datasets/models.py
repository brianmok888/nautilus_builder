from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.auth import ScopedArtifactRef


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

    @field_validator("catalog_path")
    @classmethod
    def normalize_catalog_path(cls, value: str) -> str:
        return Path(value).expanduser().as_posix()

    @property
    def scoped_artifact(self) -> ScopedArtifactRef:
        return ScopedArtifactRef(
            artifact_type="CatalogDataset",
            artifact_id=self.dataset_id,
            user_id=self.user_id,
            project_id=self.project_id,
        )
