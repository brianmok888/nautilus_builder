"""FastAPI settings — centralizes configuration for the API layer."""
from __future__ import annotations

import os


def get_builder_env() -> str:
    """Get the effective BUILDER_ENV, considering APP_ENV fallback."""
    return os.environ.get("BUILDER_ENV") or os.environ.get("APP_ENV") or "local"


def get_api_token() -> str | None:
    """Get the configured API token."""
    return os.environ.get("BUILDER_API_TOKEN")


def is_local_env() -> bool:
    """Check if running in local development mode."""
    return get_builder_env() == "local"
