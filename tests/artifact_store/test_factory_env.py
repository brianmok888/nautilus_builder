from __future__ import annotations

from pathlib import Path


def test_local_artifact_factory_honors_builder_artifact_root(monkeypatch, tmp_path: Path) -> None:
    from packages.artifact_store.factory import create_artifact_store
    from packages.artifact_store.service import LocalJsonArtifactStore

    artifact_root = tmp_path / "configured-artifacts"
    monkeypatch.setenv("BUILDER_ARTIFACT_BACKEND", "local")
    monkeypatch.setenv("BUILDER_ARTIFACT_ROOT", artifact_root.as_posix())

    store = create_artifact_store()

    assert isinstance(store, LocalJsonArtifactStore)
    assert store.root == artifact_root
