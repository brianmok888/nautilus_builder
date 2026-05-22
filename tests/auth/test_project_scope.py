import pytest

from packages.auth import (
    ProjectScopeError,
    ScopedArtifactRef,
    UserProjectContext,
    assert_same_project,
)


def test_same_project_artifact_access_is_allowed() -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    artifact = ScopedArtifactRef(
        artifact_type="StrategySpec",
        artifact_id="spec_001",
        user_id="user_123",
        project_id="project_alpha",
    )

    assert_same_project(context, artifact)


@pytest.mark.parametrize(
    ("artifact_type", "artifact_id"),
    [
        ("StrategySpec", "spec_001"),
        ("BacktestJob", "job_001"),
        ("RuntimeEvent", "event_001"),
        ("PromotionRequest", "promotion_001"),
    ],
)
def test_artifact_refs_carry_user_project_scope(artifact_type: str, artifact_id: str) -> None:
    artifact = ScopedArtifactRef(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        user_id="user_123",
        project_id="project_alpha",
    )

    assert artifact.user_id == "user_123"
    assert artifact.project_id == "project_alpha"


def test_cross_project_artifact_access_is_rejected() -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    artifact = ScopedArtifactRef(
        artifact_type="BacktestJob",
        artifact_id="job_001",
        user_id="user_123",
        project_id="project_beta",
    )

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        assert_same_project(context, artifact)


def test_cross_user_artifact_access_is_rejected() -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    artifact = ScopedArtifactRef(
        artifact_type="PromotionRequest",
        artifact_id="promotion_001",
        user_id="user_999",
        project_id="project_alpha",
    )

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        assert_same_project(context, artifact)
