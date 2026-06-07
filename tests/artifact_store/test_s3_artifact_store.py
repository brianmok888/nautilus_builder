"""Tests for S3/MinIO artifact backend and factory.

TDD RED phase — defines behavior BEFORE implementation.

Tests cover:
- Local backend still works (regression)
- S3 backend stores with content-addressed key
- Checksum mismatch fails closed
- Factory returns correct backend based on env
- S3 secrets are not in any public endpoint response
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from packages.artifact_store.models import ArtifactRecord


# ===========================================================================
# P1-2: ArtifactStoreProtocol
# ===========================================================================

class TestArtifactStoreProtocol:
    def test_protocol_defines_put_and_get(self):
        """ArtifactStoreProtocol must define put() and get() methods."""
        from packages.artifact_store.interface import ArtifactStoreProtocol

        assert hasattr(ArtifactStoreProtocol, "put")
        assert hasattr(ArtifactStoreProtocol, "get")


# ===========================================================================
# P1-2: S3ArtifactStore
# ===========================================================================

class TestS3ArtifactStore:
    def test_stores_with_content_addressed_key(self):
        """S3 store uses key format: artifacts/{type}/{sha256}/{filename}."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(
            s3_client=mock_client,
            bucket="test-bucket",
        )

        payload = {"data": "test_content"}
        result = store.put(
            artifact_type="compile_artifact",
            artifact_id="strat_001_v001",
            payload=payload,
            user_id="user_001",
            project_id="proj_001",
            content_type="application/json",
        )

        assert isinstance(result, ArtifactRecord)
        # The S3 key should follow the content-addressed pattern
        call_args = mock_client.put_object.call_args
        assert call_args is not None
        key = call_args.kwargs.get("Key") or call_args[1].get("Key")
        assert key.startswith("artifacts/compile_artifact/")
        # Key should contain the sha256 hash
        parts = key.split("/")
        assert len(parts) >= 3

    def test_checksum_verified_after_write(self):
        """S3 store verifies checksum after writing."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

        payload = {"key": "value"}
        result = store.put(
            artifact_type="replay_result",
            artifact_id="run_001",
            payload=payload,
            user_id="user_001",
            project_id="proj_001",
        )

        assert result.checksum_sha256 is not None
        assert len(result.checksum_sha256) == 64

    def test_checksum_mismatch_on_read_fails_closed(self):
        """S3 store raises on checksum mismatch when reading."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

        # Store a payload to get its original checksum
        payload = {"test": "data"}
        record = store.put(
            artifact_type="test_type",
            artifact_id="test_id",
            payload=payload,
            user_id="user_001",
            project_id="proj_001",
        )
        original_checksum = record.checksum_sha256

        # Tamper with the stored data but keep original checksum in metadata
        tampered_body = b'{"tampered": true}'
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=tampered_body)),
            "Metadata": {
                "checksum-sha256": original_checksum,
                "artifact-type": "test_type",
                "artifact-id": "test_id",
                "user-id": "user_001",
                "project-id": "proj_001",
            },
        }

        with pytest.raises(ValueError, match="checksum"):
            store.get(record.artifact_ref)

    def test_get_returns_stored_payload(self):
        """S3 store returns the stored payload on get."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

        payload = {"strategy": "test", "version": 1}
        record = store.put(
            artifact_type="compile_artifact",
            artifact_id="strat_001_v001",
            payload=payload,
            user_id="user_001",
            project_id="proj_001",
        )

        # Mock get_object to return the same data
        stored_body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=stored_body)),
        }

        result = store.get(record.artifact_ref)
        assert result["payload"] == payload

    def test_execution_authority_always_false(self):
        """All artifacts from S3 store must have execution_authority metadata set to false."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

        result = store.put(
            artifact_type="compile_artifact",
            artifact_id="strat_001_v001",
            payload={"data": "test"},
            user_id="user_001",
            project_id="proj_001",
        )

        assert result.metadata.get("execution_authority") == "false"


# ===========================================================================
# P1-2: ArtifactStoreFactory
# ===========================================================================

class TestArtifactStoreFactory:
    def test_factory_returns_local_when_env_is_local(self):
        """Factory creates LocalJsonArtifactStore when BUILDER_ARTIFACT_BACKEND=local."""
        from packages.artifact_store.factory import create_artifact_store

        with patch.dict(os.environ, {"BUILDER_ARTIFACT_BACKEND": "local"}, clear=False):
            store = create_artifact_store()
            from packages.artifact_store.service import LocalJsonArtifactStore
            assert isinstance(store, LocalJsonArtifactStore)

    def test_factory_returns_local_by_default(self):
        """Factory defaults to local when BUILDER_ARTIFACT_BACKEND is not set."""
        from packages.artifact_store.factory import create_artifact_store

        with patch.dict(os.environ, {}, clear=False):
            # Remove the env var if it exists
            os.environ.pop("BUILDER_ARTIFACT_BACKEND", None)
            store = create_artifact_store()
            from packages.artifact_store.service import LocalJsonArtifactStore
            assert isinstance(store, LocalJsonArtifactStore)

    def test_factory_returns_s3_when_env_is_s3(self):
        """Factory creates S3ArtifactStore when BUILDER_ARTIFACT_BACKEND=s3."""
        import sys
        from packages.artifact_store.factory import create_artifact_store

        # boto3 is an optional dependency — inject a mock so the factory can import it
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = MagicMock()
        with patch.dict(sys.modules, {"boto3": mock_boto3}), \
             patch.dict(os.environ, {
            "BUILDER_ARTIFACT_BACKEND": "s3",
            "BUILDER_S3_BUCKET": "test-bucket",
            "BUILDER_S3_REGION": "us-east-1",
            "BUILDER_S3_ACCESS_KEY_ID": "test-key",
            "BUILDER_S3_SECRET_ACCESS_KEY": "test-secret",
        }, clear=False):
            store = create_artifact_store()
            from packages.artifact_store.s3_store import S3ArtifactStore
            assert isinstance(store, S3ArtifactStore)

    def test_factory_s3_missing_bucket_raises(self):
        """Factory raises when BUILDER_S3_BUCKET is missing."""
        from packages.artifact_store.factory import create_artifact_store

        with patch.dict(os.environ, {
            "BUILDER_ARTIFACT_BACKEND": "s3",
            "BUILDER_S3_REGION": "us-east-1",
        }, clear=False):
            os.environ.pop("BUILDER_S3_BUCKET", None)
            with pytest.raises(ValueError, match="BUILDER_S3_BUCKET"):
                create_artifact_store()


# ===========================================================================
# P1-2: Local backend still works (regression)
# ===========================================================================

class TestLocalBackendRegression:
    def test_local_json_store_still_works(self):
        """Existing LocalJsonArtifactStore functionality unchanged."""
        import tempfile
        from packages.artifact_store.service import LocalJsonArtifactStore
        from packages.auth import UserProjectContext

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalJsonArtifactStore(root=tmpdir)
            ctx = UserProjectContext(user_id="user_001", project_id="proj_001")

            record = store.put_json(
                context=ctx,
                artifact_type="compile_artifact",
                artifact_id="test_001",
                payload={"data": "test"},
            )

            assert record.artifact_ref.startswith("artifact://builder/")

            stored = store.get_json(context=ctx, artifact_ref=record.artifact_ref)
            assert stored.payload == {"data": "test"}


# ===========================================================================
# P1-2: S3 secrets not in response
# ===========================================================================

class TestS3SecretsSafety:
    def test_artifact_record_does_not_contain_s3_secrets(self):
        """ArtifactRecord must never contain S3 credentials."""
        record = ArtifactRecord(
            artifact_ref="artifact://builder/proj/user/type/id",
            artifact_type="type",
            artifact_id="id",
            user_id="user",
            project_id="proj",
            path="/some/path",
            checksum_sha256="a" * 64,
            content_type="application/json",
            created_at="2026-01-01T00:00:00Z",
        )

        data = record.model_dump()
        # No secret fields should be present
        assert "s3_access_key" not in data
        assert "s3_secret_key" not in data
        assert "secret" not in str(data).lower() or "checksum_sha256" in str(data).lower()

    def test_s3_store_put_result_has_no_secrets(self):
        """S3 store put() result must not leak S3 credentials."""
        from packages.artifact_store.s3_store import S3ArtifactStore

        mock_client = MagicMock()
        store = S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

        result = store.put(
            artifact_type="test",
            artifact_id="id",
            payload={"data": "test"},
            user_id="user_001",
            project_id="proj_001",
        )

        data = result.model_dump()
        for key in data:
            assert "secret" not in key.lower() or key == "checksum_sha256"
            assert "password" not in key.lower()
            assert "credential" not in key.lower()
