from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserProjectContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    role: str = "builder"


class AuthToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)
    context: UserProjectContext


class ScopedArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
