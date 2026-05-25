from __future__ import annotations

import json

import pytest

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import ProjectScopeError, UserProjectContext


def test_json_artifacts_persist_with_scoped_ref_and_checksum(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store = LocalJsonArtifactStore(root=tmp_path)

    record = store.put_json(
        context=context,
        artifact_type="backtest_result",
        artifact_id="result_001",
        payload={"metric": 1.25, "orders": 0},
        metadata={"job_id": "bt_001"},
    )

    assert record.artifact_ref == "artifact://builder/project_alpha/user_123/backtest_result/result_001"
    assert record.checksum_sha256
    assert record.metadata["job_id"] == "bt_001"
    assert json.loads((tmp_path / "project_alpha" / "user_123" / "backtest_result" / "result_001.json").read_text())["payload"]["orders"] == 0

    reopened = LocalJsonArtifactStore(root=tmp_path)
    loaded = reopened.get_json(context=context, artifact_ref=record.artifact_ref)

    assert loaded.record == record
    assert loaded.payload == {"metric": 1.25, "orders": 0}


def test_json_artifact_reads_reject_cross_project_scope(tmp_path) -> None:
    owner = UserProjectContext(user_id="user_123", project_id="project_alpha")
    intruder = UserProjectContext(user_id="user_123", project_id="project_beta")
    store = LocalJsonArtifactStore(root=tmp_path)
    record = store.put_json(
        context=owner,
        artifact_type="backtest_result",
        artifact_id="result_001",
        payload={"orders": 0},
    )

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        store.get_json(context=intruder, artifact_ref=record.artifact_ref)


def test_json_artifact_store_rejects_path_traversal_identifiers(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store = LocalJsonArtifactStore(root=tmp_path)

    with pytest.raises(ValueError, match="safe identifier"):
        store.put_json(
            context=context,
            artifact_type="backtest_result",
            artifact_id="../escape",
            payload={"orders": 0},
        )
