# Storage config supports a legacy schema alias (without shadow_field)
# DEPRECATED: legacy alias will be removed after 2026-07-01.
# Tracking issue: see handguard.md §19 legacy/deprecation closure schedule.
# All new storage configs must include shadow_field.
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SAFE_STORAGE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def safe_storage_identifier(value: str) -> str:
    if _SAFE_STORAGE_IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"safe storage identifier required: {value}")
    return value


class BuilderPostgresConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    dsn_env: str = Field(min_length=1)
    db_schema: str = Field(default="builder", min_length=1, alias="schema")

    @field_validator("db_schema")
    @classmethod
    def validate_schema(cls, value: str) -> str:
        return safe_storage_identifier(value)

    def table_name(self, table: str) -> str:
        safe_table = safe_storage_identifier(table)
        return f"{self.db_schema}.{safe_table}"


class BuilderRedisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url_env: str = Field(min_length=1)
    namespace: str = Field(default="builder", min_length=1)

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, value: str) -> str:
        return safe_storage_identifier(value)

    @model_validator(mode="after")
    def reject_nd_namespace(self) -> "BuilderRedisConfig":
        if self.namespace == "nd":
            raise ValueError("Builder Redis namespace must not be nd")
        return self

    def stream(self, suffix: str) -> str:
        normalized = suffix.strip(":")
        return f"{self.namespace}:{normalized}"
