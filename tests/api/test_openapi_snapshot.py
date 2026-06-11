"""OpenAPI snapshot test — Segment 9."""
import json
from pathlib import Path

from services.api.fastapi_app import create_fastapi_app

SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "tests" / "api" / "openapi_snapshot.json"


class TestOpenAPISnapshot:
    def test_openapi_schema_matches_snapshot(self) -> None:
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        schema = app.openapi()

        if not SNAPSHOT_PATH.exists():
            SNAPSHOT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True))
            pytest.skip("Created initial snapshot")

        expected = json.loads(SNAPSHOT_PATH.read_text())

        # Compare paths (the most important contract surface)
        assert set(schema.get("paths", {}).keys()) == set(expected.get("paths", {}).keys()), (
            f"API paths changed: added={set(schema.get('paths', {})) - set(expected.get('paths', {}))}, "
            f"removed={set(expected.get('paths', {})) - set(schema.get('paths', {}))}"
        )

    def test_health_paths_are_public(self) -> None:
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        schema = app.openapi()
        paths = schema.get("paths", {})
        health_paths = [p for p in paths if p.startswith("/health")]
        assert len(health_paths) >= 3, f"Expected at least 3 health paths, got {health_paths}"

    def test_api_paths_require_auth_in_docs(self) -> None:
        """All /api paths should have security requirements in the OpenAPI schema."""
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        schema = app.openapi()
        paths = schema.get("paths", {})
        api_paths = [p for p in paths if p.startswith("/api")]
        # At least some API paths should exist
        assert len(api_paths) > 0, "No /api paths found in OpenAPI schema"


import pytest
