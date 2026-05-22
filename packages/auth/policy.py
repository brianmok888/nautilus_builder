from __future__ import annotations

from packages.auth.models import ScopedArtifactRef, UserProjectContext


class ProjectScopeError(PermissionError):
    pass


def assert_same_project(context: UserProjectContext, artifact: ScopedArtifactRef) -> None:
    if context.user_id != artifact.user_id or context.project_id != artifact.project_id:
        raise ProjectScopeError(
            f"artifact {artifact.artifact_type}/{artifact.artifact_id} is outside user/project scope"
        )
