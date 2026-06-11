"""Tests for local object storage backend."""
from __future__ import annotations

import tempfile

import pytest

from packages.object_storage.local import LocalObjectStorage


@pytest.fixture
def storage(tmp_path):
    return LocalObjectStorage(tmp_path / "test_storage")


class TestLocalObjectStorage:
    def test_write_and_read(self, storage):
        uri = storage.write("test/artifact.json", b'{"key": "value"}')
        assert "local://" in uri
        data = storage.read("test/artifact.json")
        assert data == b'{"key": "value"}'

    def test_read_missing_returns_none(self, storage):
        assert storage.read("nonexistent") is None

    def test_exists(self, storage):
        storage.write("exists_test", b"data")
        assert storage.exists("exists_test")
        assert not storage.exists("nonexistent")

    def test_delete(self, storage):
        storage.write("delete_test", b"data")
        assert storage.delete("delete_test")
        assert not storage.exists("delete_test")
        assert not storage.delete("delete_test")

    def test_path_traversal_rejected(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.write("../../etc/passwd", b"bad")

    def test_overwrite(self, storage):
        storage.write("overwrite_test", b"v1")
        storage.write("overwrite_test", b"v2")
        assert storage.read("overwrite_test") == b"v2"

    def test_nested_keys(self, storage):
        storage.write("a/b/c/d.json", b"nested")
        assert storage.read("a/b/c/d.json") == b"nested"
