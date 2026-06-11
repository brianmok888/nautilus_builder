"""Production configuration model — Segment D v4.

Validates all required production config before the API starts.
Fails closed: missing or invalid config prevents startup.
"""
from __future__ import annotations

import json
import os
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator


_DEMO_TOKENS = {
    "demo-token-for-testing-only",
    "dev-secret-change-me",
    "change-me-in-production",
    "my-secret-prod-key-2026",
}

_MIN_TOKEN_LENGTH = 32


def _is_valid_cors(origins_str: str) -> bool:
    """CORS origins must be a non-empty JSON array without wildcards."""
    try:
        origins = json.loads(origins_str)
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(origins, list) or len(origins) == 0:
        return False
    for o in origins:
        if not isinstance(o, str) or o.strip() == "*":
            return False
    return True


class BuilderProductionConfig(BaseModel):
    """Typed production configuration with fail-closed validation."""

    model_config = ConfigDict(extra="forbid")

    builder_env: str = "production"
    api_token: str
    database_url: str
    redis_url: str
    artifact_backend: str = "s3"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    cors_origins: str = "[]"
    has_browser_api_token: bool = False

    @model_validator(mode="after")
    def _validate_production(self) -> "BuilderProductionConfig":
        # Token checks
        if not self.api_token or len(self.api_token) < _MIN_TOKEN_LENGTH:
            raise ValueError(
                f"api_token must be at least {_MIN_TOKEN_LENGTH} characters in production"
            )
        if self.api_token in _DEMO_TOKENS:
            raise ValueError(
                f"api_token must not be a demo/dev token in production"
            )

        # Database
        if not self.database_url:
            raise ValueError("database_url is required in production")

        # Redis
        if not self.redis_url:
            raise ValueError("redis_url is required in production")

        # Artifact backend
        if self.artifact_backend == "local":
            raise ValueError(
                "artifact_backend must be 's3' in production, not 'local'"
            )
        if self.artifact_backend == "s3" and not self.s3_bucket:
            raise ValueError(
                "s3_bucket is required when artifact_backend is 's3'"
            )

        # CORS
        if not _is_valid_cors(self.cors_origins):
            raise ValueError(
                "cors_origins must be a non-empty JSON array without wildcards"
            )

        # Browser token
        if self.has_browser_api_token:
            raise ValueError(
                "NEXT_PUBLIC_BUILDER_API_TOKEN must not be set in production"
            )

        return self


def validate_production_config_from_env() -> BuilderProductionConfig:
    """Build and validate production config from environment variables."""
    return BuilderProductionConfig(
        builder_env=os.environ.get("BUILDER_ENV", "production"),
        api_token=os.environ.get("BUILDER_API_TOKEN", ""),
        database_url=os.environ.get("BUILDER_DATABASE_URL", ""),
        redis_url=os.environ.get("BUILDER_REDIS_URL", ""),
        artifact_backend=os.environ.get("BUILDER_ARTIFACT_BACKEND", "local"),
        s3_bucket=os.environ.get("BUILDER_S3_BUCKET", ""),
        s3_endpoint_url=os.environ.get("BUILDER_S3_ENDPOINT_URL", ""),
        s3_access_key=os.environ.get("BUILDER_S3_ACCESS_KEY", ""),
        s3_secret_key=os.environ.get("BUILDER_S3_SECRET_KEY", ""),
        cors_origins=os.environ.get("BUILDER_CORS_ORIGINS", "[]"),
        has_browser_api_token=bool(os.environ.get("NEXT_PUBLIC_BUILDER_API_TOKEN", "")),
    )
