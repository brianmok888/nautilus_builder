from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse


def _install_fake_fastapi(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))


def _seed_shadow_evidence_refs(artifact_root: Path) -> tuple[dict[str, str], object, object]:
    from packages.artifact_store import LocalJsonArtifactStore
    from packages.auth import AuthTokenService, UserProjectContext

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store = LocalJsonArtifactStore(root=artifact_root)
    refs: dict[str, str] = {}
    for artifact_type in (
        "validation_report",
        "backtest_result",
        "no_lookahead_report",
        "gate_compatibility_report",
        "runtime_boundary_report",
        "risk_review",
    ):
        refs[artifact_type] = store.put_json(
            context=context,
            artifact_type=artifact_type,
            artifact_id=f"{artifact_type}_001",
            payload={
                "evidence_type": artifact_type,
                "compile_hash": "abc123",
                "strategy_version": "0.3.0-beta.1",
                "orders": 0,
            },
            metadata={"compile_hash": "abc123", "strategy_version": "0.3.0-beta.1"},
        ).artifact_ref
    return refs, auth, token


def test_fastapi_uses_default_artifact_store_from_builder_artifact_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _install_fake_fastapi(monkeypatch)
    artifact_root = tmp_path / "builder-artifacts"
    refs, auth, token = _seed_shadow_evidence_refs(artifact_root)
    monkeypatch.setenv("BUILDER_ARTIFACT_BACKEND", "local")
    monkeypatch.setenv("BUILDER_ARTIFACT_ROOT", artifact_root.as_posix())

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app(auth_token_service=auth)
    response = app.routes[("POST", "/api/promotions/shadow")](
        {
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": refs,
        },
        authorization=f"Bearer {token.token}",
    )

    assert response.status_code == 201
    assert set(response.json()["evidence_checksums"]) == set(refs)


def test_fastapi_readiness_reports_artifact_store_factory_failure(monkeypatch) -> None:
    _install_fake_fastapi(monkeypatch)
    monkeypatch.setenv("BUILDER_ARTIFACT_BACKEND", "s3")
    monkeypatch.delenv("BUILDER_S3_BUCKET", raising=False)

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()
    ready = app.routes[("GET", "/health/ready")]()

    assert ready["ready"] is False
    assert ready["checks"]["artifact_store"] == "error"


def test_fastapi_postgres_llm_config_save_persists_to_config_repository(
    monkeypatch,
) -> None:
    _install_fake_fastapi(monkeypatch)
    monkeypatch.setenv("BUILDER_DATABASE_URL", "postgresql://builder:test@localhost/builder")

    import packages.postgres as postgres
    from packages.auth import AuthTokenService

    class RecordingConfigRepository:
        instances: list["RecordingConfigRepository"] = []

        def __init__(self, conn: object) -> None:
            self.saved: list[tuple[str, dict[str, Any], str | None]] = []
            self.instances.append(self)

        def get(self, key: str) -> dict[str, Any] | None:
            assert key == "llm_config"
            return None

        def set(self, key: str, value: dict[str, Any], *, updated_by: str | None = None) -> None:
            self.saved.append((key, value, updated_by))

    monkeypatch.setattr(postgres, "connect_pool", lambda dsn: object())
    monkeypatch.setattr(postgres, "apply_migrations", lambda conn: None)
    monkeypatch.setattr(postgres, "seed_default_market_data", lambda conn: None)
    monkeypatch.setattr(postgres, "PostgresConfigRepository", RecordingConfigRepository)

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    payload = {
        "provider_type": "local-openai-compatible",
        "base_url": "http://127.0.0.1:11434/v1",
        "draft_model": "qwen-strategy-draft",
        "validation_model": "qwen-strategy-validate",
        "explanation_model": "qwen-strategy-explain",
    }

    app = create_fastapi_app(auth_token_service=auth)
    response = app.routes[("POST", "/api/config/llm")](payload, authorization=f"Bearer {token.token}")

    assert response.status_code == 200
    assert RecordingConfigRepository.instances[0].saved == [("llm_config", payload, None)]
