"""Production auth policy matrix tests — Segment 10."""
import os
import pytest


class TestProductionPolicyMatrix:
    def test_local_allows_dev_token(self) -> None:
        from packages.auth.policy import validate_builder_env, BuilderEnvironment
        result = validate_builder_env("local")
        assert result == BuilderEnvironment.LOCAL

    def test_production_rejects_short_token(self) -> None:
        os.environ["BUILDER_ENV"] = "production"
        os.environ["BUILDER_API_TOKEN"] = "short"
        try:
            from packages.auth.policy import validate_production_token
            with pytest.raises(Exception):
                validate_production_token()
        finally:
            os.environ.pop("BUILDER_API_TOKEN", None)
            os.environ.pop("BUILDER_ENV", None)

    def test_production_rejects_next_public_token(self) -> None:
        os.environ["BUILDER_ENV"] = "production"
        os.environ["NEXT_PUBLIC_BUILDER_API_TOKEN"] = "should-not-exist"
        try:
            from packages.auth.policy import validate_production_token
            with pytest.raises(Exception):
                validate_production_token()
        finally:
            os.environ.pop("NEXT_PUBLIC_BUILDER_API_TOKEN", None)
            os.environ.pop("BUILDER_ENV", None)

    def test_production_rejects_wildcard_cors(self) -> None:
        os.environ["BUILDER_ENV"] = "production"
        try:
            from packages.auth.policy import validate_cors_config
            with pytest.raises(Exception):
                validate_cors_config()
        finally:
            os.environ.pop("BUILDER_ENV", None)

    def test_local_env_validation(self) -> None:
        from packages.auth.policy import validate_builder_env, BuilderEnvironment
        result = validate_builder_env("local")
        assert result == BuilderEnvironment.LOCAL

    def test_staging_env_validation(self) -> None:
        from packages.auth.policy import validate_builder_env, BuilderEnvironment
        result = validate_builder_env("staging")
        assert result == BuilderEnvironment.STAGING

    def test_invalid_env_raises(self) -> None:
        from packages.auth.policy import validate_builder_env
        with pytest.raises(ValueError, match="unknown BUILDER_ENV"):
            validate_builder_env("invalid_env")
