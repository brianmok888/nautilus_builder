from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_ref: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    content_type: str = "application/json"
    created_at: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class StoredJsonArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record: ArtifactRecord
    payload: dict[str, object]
