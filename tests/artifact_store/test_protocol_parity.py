"""Tests for unified ArtifactStoreProtocol parity across Local and S3 stores.

v6 Segment 05: Both stores must expose put_json/get_json/verify_ref
with the same UserProjectContext-based interface.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from packages.artifact_store.models import ArtifactRecord, StoredJsonArtifact
from packages.auth import UserProjectContext


def _make_context(
    user_id: str = "u1",
    project_id: str = "proj-1",
) -> UserProjectContext:
    return UserProjectContext(user_id=user_id, project_id=project_id)


class TestLocalStoreProtocolParity:
    def test_put_json_returns_artifact_record(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"test": True},
        )
        assert isinstance(record, ArtifactRecord)
        assert record.artifact_type == "compile_artifact"
        assert record.project_id == "proj-1"
        assert len(record.checksum_sha256) == 64

    def test_get_json_returns_stored_artifact(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"value": 42},
        )
        result = store.get_json(context=ctx, artifact_ref=record.artifact_ref)
        assert isinstance(result, StoredJsonArtifact)
        assert result.payload == {"value": 42}

    def test_verify_ref_passes_for_valid_artifact(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        result = store.verify_ref(context=ctx, artifact_ref=record.artifact_ref)
        assert isinstance(result, ArtifactRecord)

    def test_verify_ref_with_expected_sha256_passes(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        result = store.verify_ref(
            context=ctx,
            artifact_ref=record.artifact_ref,
            expected_sha256=record.checksum_sha256,
        )
        assert isinstance(result, ArtifactRecord)

    def test_verify_ref_with_wrong_sha256_raises(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        with pytest.raises(ValueError, match="checksum mismatch"):
            store.verify_ref(
                context=ctx,
                artifact_ref=record.artifact_ref,
                expected_sha256="b" * 64,
            )

    def test_get_json_wrong_project_raises(self, tmp_path):
        from packages.artifact_store.service import LocalJsonArtifactStore
        store = LocalJsonArtifactStore(root=str(tmp_path))
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        wrong_ctx = _make_context(project_id="proj-2")
        with pytest.raises((ValueError, Exception)):
            store.get_json(context=wrong_ctx, artifact_ref=record.artifact_ref)


class TestS3StoreProtocolParity:
    def _make_s3_store(self):
        """Create S3ArtifactStore with mock client."""
        from packages.artifact_store.s3_store import S3ArtifactStore
        mock_client = _MockS3Client()
        return S3ArtifactStore(s3_client=mock_client, bucket="test-bucket")

    def test_put_json_returns_artifact_record(self):
        store = self._make_s3_store()
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"test": True},
        )
        assert isinstance(record, ArtifactRecord)
        assert record.artifact_type == "compile_artifact"
        assert record.project_id == "proj-1"
        assert len(record.checksum_sha256) == 64

    def test_get_json_returns_stored_artifact(self):
        store = self._make_s3_store()
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"value": 42},
        )
        result = store.get_json(context=ctx, artifact_ref=record.artifact_ref)
        assert isinstance(result, StoredJsonArtifact)
        assert result.payload == {"value": 42}

    def test_verify_ref_passes_for_valid_artifact(self):
        store = self._make_s3_store()
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        result = store.verify_ref(context=ctx, artifact_ref=record.artifact_ref)
        assert isinstance(result, ArtifactRecord)

    def test_verify_ref_with_wrong_sha256_raises(self):
        store = self._make_s3_store()
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        with pytest.raises(ValueError, match="checksum mismatch"):
            store.verify_ref(
                context=ctx,
                artifact_ref=record.artifact_ref,
                expected_sha256="b" * 64,
            )

    def test_get_json_wrong_project_raises(self):
        store = self._make_s3_store()
        ctx = _make_context()
        record = store.put_json(
            context=ctx,
            artifact_type="compile_artifact",
            artifact_id="art-001",
            payload={"ok": True},
        )
        wrong_ctx = _make_context(project_id="proj-2")
        with pytest.raises(ValueError, match="scope"):
            store.get_json(context=wrong_ctx, artifact_ref=record.artifact_ref)


class TestFactoryRejectsUnknown:
    def test_factory_rejects_unknown_backend(self, monkeypatch):
        from packages.artifact_store.factory import create_artifact_store
        monkeypatch.setenv("BUILDER_ARTIFACT_BACKEND", "ftp")
        with pytest.raises(ValueError, match="Unknown"):
            create_artifact_store()

    def test_factory_rejects_s3_without_bucket_in_production(self, monkeypatch):
        from packages.artifact_store.factory import create_artifact_store
        monkeypatch.setenv("BUILDER_ARTIFACT_BACKEND", "s3")
        monkeypatch.setenv("BUILDER_S3_BUCKET", "")
        with pytest.raises(ValueError, match="BUILDER_S3_BUCKET"):
            create_artifact_store()


class _MockS3Client:
    """Minimal mock S3 client for testing."""

    def __init__(self) -> None:
        self._objects: dict[str, dict[str, Any]] = {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str, Metadata: dict[str, str]) -> None:
        self._objects[Key] = {
            "Body": Body,
            "ContentType": ContentType,
            "Metadata": Metadata,
        }

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self._objects:
            raise ValueError(f"No such key: {Key}")
        obj = self._objects[Key]
        return {
            "Body": _MockBody(obj["Body"]),
            "ContentType": obj["ContentType"],
            "Metadata": obj["Metadata"],
        }


class _MockBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data
