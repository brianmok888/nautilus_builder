from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from packages.auth import ScopedArtifactRef, UserProjectContext, assert_same_project

from .models import ArtifactRecord, StoredJsonArtifact

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_ARTIFACT_PREFIX = "artifact://builder"


class LocalJsonArtifactStore:
    """Durable local JSON artifact store with Builder user/project scope."""

    def __init__(self, *, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_json(
        self,
        *,
        context: UserProjectContext,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        metadata: dict[str, str] | None = None,
    ) -> ArtifactRecord:
        safe_type = _safe_identifier(artifact_type)
        safe_id = _safe_identifier(artifact_id)
        payload_json = _canonical_json(payload)
        checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        path = self._path_for(
            project_id=context.project_id,
            user_id=context.user_id,
            artifact_type=safe_type,
            artifact_id=safe_id,
        )
        record = ArtifactRecord(
            artifact_ref=self._artifact_ref(
                project_id=context.project_id,
                user_id=context.user_id,
                artifact_type=safe_type,
                artifact_id=safe_id,
            ),
            artifact_type=safe_type,
            artifact_id=safe_id,
            user_id=context.user_id,
            project_id=context.project_id,
            path=path.as_posix(),
            checksum_sha256=checksum,
            created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            metadata=dict(metadata or {}),
        )
        envelope = {"record": record.model_dump(mode="json"), "payload": payload}
        self._atomic_write(path, _canonical_json(envelope))
        return record

    def get_json(self, *, context: UserProjectContext, artifact_ref: str) -> StoredJsonArtifact:
        scoped = self.scoped_ref(artifact_ref)
        assert_same_project(context, scoped)
        path = self._path_for(
            project_id=scoped.project_id,
            user_id=scoped.user_id,
            artifact_type=scoped.artifact_type,
            artifact_id=scoped.artifact_id,
        )
        try:
            raw = path.read_text()
        except FileNotFoundError as exc:
            raise ValueError(f"artifact not found: {artifact_ref}") from exc
        try:
            envelope = json.loads(raw)
            if not isinstance(envelope, dict):
                raise ValueError("artifact envelope must be an object")
            record = ArtifactRecord.model_validate(envelope["record"])
            payload = dict(envelope["payload"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"artifact envelope invalid: {artifact_ref}") from exc
        assert_same_project(context, self.scoped_ref(record.artifact_ref))
        checksum = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        if checksum != record.checksum_sha256:
            raise ValueError(f"artifact checksum mismatch: {record.artifact_ref}")
        return StoredJsonArtifact(record=record, payload=payload)

    def scoped_ref(self, artifact_ref: str) -> ScopedArtifactRef:
        parts = artifact_ref.split("/")
        if len(parts) != 7 or "/".join(parts[:3]) != _ARTIFACT_PREFIX:
            raise ValueError("invalid Builder artifact ref")
        _, _, _, project_id, user_id, artifact_type, artifact_id = parts
        return ScopedArtifactRef(
            artifact_type=_safe_identifier(artifact_type),
            artifact_id=_safe_identifier(artifact_id),
            user_id=_safe_identifier(user_id),
            project_id=_safe_identifier(project_id),
        )

    def _path_for(self, *, project_id: str, user_id: str, artifact_type: str, artifact_id: str) -> Path:
        safe_project = _safe_identifier(project_id)
        safe_user = _safe_identifier(user_id)
        safe_type = _safe_identifier(artifact_type)
        safe_id = _safe_identifier(artifact_id)
        path = self.root / safe_project / safe_user / safe_type / f"{safe_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _artifact_ref(*, project_id: str, user_id: str, artifact_type: str, artifact_id: str) -> str:
        return f"{_ARTIFACT_PREFIX}/{project_id}/{user_id}/{artifact_type}/{artifact_id}"

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temp_name = handle.name
        Path(temp_name).replace(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _safe_identifier(value: str) -> str:
    if _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"safe identifier required: {value}")
    return value
