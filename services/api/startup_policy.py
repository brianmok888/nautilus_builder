"""Startup policy — validates production config before API starts.

Segment D v4: Production API refuses to boot with invalid config.
"""
from __future__ import annotations

import os

from packages.config.production import BuilderProductionConfig, validate_production_config_from_env


def validate_startup_policy() -> BuilderProductionConfig | None:
    """Validate startup policy based on environment.

    Returns:
        BuilderProductionConfig if in production/staging, None if local/dev.

    Raises:
        ValueError: If production/staging config is invalid.
    """
    env = os.environ.get("BUILDER_ENV", os.environ.get("APP_ENV", "local"))
    if env in ("local", "development", "dev"):
        return None

    # Production or staging — validate full config
    config = validate_production_config_from_env()
    return config


def is_production() -> bool:
    """Check if running in production mode."""
    env = os.environ.get("BUILDER_ENV", os.environ.get("APP_ENV", "local"))
    return env in ("production", "staging")
