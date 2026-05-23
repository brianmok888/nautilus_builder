from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BuilderPostgresConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dsn_env: str = Field(min_length=1)
    schema: str = Field(default="builder", min_length=1)

    def table_name(self, table: str) -> str:
        return f"{self.schema}.{table}"


class BuilderRedisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url_env: str = Field(min_length=1)
    namespace: str = Field(default="builder", min_length=1)

    @model_validator(mode="after")
    def reject_nd_namespace(self) -> "BuilderRedisConfig":
        if self.namespace == "nd":
            raise ValueError("Builder Redis namespace must not be nd")
        return self

    def stream(self, suffix: str) -> str:
        normalized = suffix.strip(":")
        return f"{self.namespace}:{normalized}"
