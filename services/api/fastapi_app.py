from __future__ import annotations

import os
import sqlite3
from typing import Any, Callable, Protocol

from packages.ai_builder.provider import DraftAuditStoreProtocol, RecordedAiDraftStore, SqliteAiDraftAuditStore
from packages.ai_builder.service import AiBuilderService
from packages.artifact_store import LocalJsonArtifactStore, create_artifact_store
from packages.auth import AuthTokenService, InvalidAuthTokenError, ProjectScopeError, UserProjectContext
from packages.auth.policy import BuilderEnvironment, validate_builder_env, validate_cors_config, validate_production_token, validate_rate_limit_config
from packages.auth.audit_middleware import AuditMiddleware, AuthContextMiddleware, RequestIdMiddleware
from packages.auth.rate_limit import InMemoryRateLimiter
from packages.auth.redis_rate_limit import RedisRateLimiter
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDatasetRegistryService
from packages.execution_lane import ExecutionLaneService
from packages.llm_config import LlmConfigService
from packages.strategy_spec.repository import InMemoryStrategyRepository
from packages.workflow_spine import InMemoryWorkflowRepository
from services.api.routes.ai_builder import apply_ai_draft_payload, generate_ai_draft_payload
from services.api.routes.backtest_jobs import backtest_job_events_payload, backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload
from services.api.routes.backtest_execution import run_backtest_job_payload
from services.api.routes.pipeline import run_pipeline_payload, promote_pipeline_payload
from services.api.routes.execution_lane import create_execution_lane_credential_slot_payload, enqueue_execution_lane_command_payload, execution_lane_runtime_plan_payload, execution_lane_session_payload, register_execution_lane_profile_payload, run_execution_lane_worker_once_payload, start_execution_lane_paper_session_payload, stop_execution_lane_session_payload
from services.api.router import ApiResponse
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.llm_config import get_llm_config_payload, save_llm_config_payload
from packages.runtime_events.service import RuntimeEventService
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.promotions import create_shadow_payload, request_promotion_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads
from services.api.routes.strategies import create_strategy_payload, create_strategy_version_payload, list_strategies_payload, strategy_detail_payload, update_strategy_draft_payload
from services.api.routes.evidence_summary import strategy_evidence_summary_payload
from services.api.routes.workflow_results import (
    list_results_payload,
    workflow_lineage_status_payload,
    workflow_result_payload,
    workflow_result_suggestions_payload,
)



class _RateLimiterProtocol(Protocol):
    def is_allowed(self, key: str) -> bool:
        ...


class _PgWorkflowAdapter:
    """Thin adapter that delegates workflow result operations to Postgres
    while falling back to InMemoryWorkflowRepository for other methods."""

    def __init__(self, pg_result_repo, fallback_repo):
        self._pg = pg_result_repo
        self._fallback = fallback_repo

    def save_result(self, record):
        self._fallback.save_result(record)
        self._pg.save_result(record)

    def result(self, result_id, *, context=None):
        from packages.auth import ProjectScopeError
        rec = self._pg.result(result_id)
        if rec is not None and context is not None and rec.project_id != context.project_id:
            raise ProjectScopeError(f"result {result_id} is outside project scope")
        return rec if rec is not None else self._fallback.result(result_id, context=context)

    def result_for_job(self, test_job_id):
        rec = self._pg.result_for_job(test_job_id)
        return rec if rec is not None else self._fallback.result_for_job(test_job_id)

    def list_results(self, *, limit=None, offset=0, context=None):
        return self._pg.list_results(limit=limit, offset=offset, context=context)

    def results_for_lineage(self, strategy_lineage_id):
        return self._pg.results_for_lineage(strategy_lineage_id)

    def save_strategy(self, strategy):
        return self._fallback.save_strategy(strategy)

    def save_version(self, version):
        return self._fallback.save_version(version)

    def save_job(self, job):
        return self._fallback.save_job(job)

    def strategy(self, strategy_id):
        return self._fallback.strategy(strategy_id)

    def version(self, strategy_version_id):
        return self._fallback.version(strategy_version_id)

    def job(self, test_job_id):
        return self._fallback.job(test_job_id)

    def save_suggestion(self, suggestion):
        return self._fallback.save_suggestion(suggestion)

    def suggestions(self, result_id):
        return self._fallback.suggestions(result_id)

def create_fastapi_app(
    workflow_repository: InMemoryWorkflowRepository | None = None,
    strategy_repository: InMemoryStrategyRepository | None = None,
    backtest_job_service: BacktestJobService | None = None,
    auth_token_service: AuthTokenService | None = None,
    catalog_dataset_registry: CatalogDatasetRegistryService | None = None,
    artifact_store: LocalJsonArtifactStore | None = None,
    ai_audit_store: DraftAuditStoreProtocol | None = None,
    execution_lane_service: ExecutionLaneService | None = None,
    llm_config_service: LlmConfigService | None = None,
    runtime_event_service: RuntimeEventService | None = None,
    rate_limiter: _RateLimiterProtocol | None = None,
    audit_writer: Callable[[dict[str, Any]], None] | None = None,
):
    from fastapi import FastAPI, Header
    from fastapi.responses import JSONResponse

    _validate_startup_policy()
    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
    strategy_repository = strategy_repository or InMemoryStrategyRepository()

    # Postgres: when BUILDER_DATABASE_URL is set, use real persistence
    import os
    import logging
    _log = logging.getLogger(__name__)
    _pg_dsn = os.environ.get("BUILDER_DATABASE_URL", "").strip()
    _pg_conn = None
    _pg_adapter_repo = None
    _pg_config_repo = None
    if _pg_dsn:
        from packages.postgres import connect_pool, apply_migrations, PostgresStrategyRepository, PostgresAdapterRepository, PostgresBacktestJobRepository, PostgresConfigRepository, PostgresWorkflowResultRepository, seed_default_market_data
        _pg_conn = connect_pool(_pg_dsn)
        apply_migrations(_pg_conn)
        strategy_repository = PostgresStrategyRepository(_pg_conn)
        _pg_adapter_repo = PostgresAdapterRepository(_pg_conn)
        seed_default_market_data(_pg_conn)
        # Replace in-memory services with Postgres-backed implementations
        if backtest_job_service is None:
            from packages.backtest_jobs.postgres_service import PostgresBacktestJobService
            _pg_bt_repo = PostgresBacktestJobRepository(_pg_conn)
            backtest_job_service = PostgresBacktestJobService(_pg_bt_repo)
        # Replace in-memory workflow repository with Postgres-backed
        _pg_workflow_repo = PostgresWorkflowResultRepository(_pg_conn)
        # Wrap with a thin adapter that delegates to PG
        workflow_repository = _PgWorkflowAdapter(_pg_workflow_repo, workflow_repository)
        # LLM config: load from Postgres if available
        _pg_config_repo = PostgresConfigRepository(_pg_conn)
        if llm_config_service is None:
            _saved_config = _pg_config_repo.get("llm_config")
            if _saved_config:
                from packages.llm_config.models import LlmConfig
                try:
                    llm_config_service = LlmConfigService(LlmConfig.model_validate(_saved_config))
                except Exception:
                    llm_config_service = LlmConfigService()
            else:
                llm_config_service = LlmConfigService()
        if os.environ.get("BUILDER_SEED_DEMO_STRATEGIES", "").strip().lower() in ("1", "true", "yes"):
            from scripts.seed_demo_evidence import seed_demo_evidence
            seed_demo_evidence(strategy_repository, backtest_job_service, context=_env_user_project_context())
    elif os.environ.get("BUILDER_SEED_DEMO_STRATEGIES", "").strip().lower() in ("1", "true", "yes"):
        backtest_job_service = backtest_job_service or BacktestJobService()
        from scripts.seed_demo_evidence import seed_demo_evidence
        seed_demo_evidence(strategy_repository, backtest_job_service, context=_env_user_project_context())
        _log.warning("Running with in-memory Builder repositories. State will not survive restart.")
    else:
        backtest_job_service = backtest_job_service or BacktestJobService()
        _log.warning("Running with in-memory Builder repositories. State will not survive restart.")
    auth_token_service = auth_token_service or AuthTokenService()
    _register_env_dev_token(auth_token_service)
    catalog_dataset_registry = catalog_dataset_registry or CatalogDatasetRegistryService()
    artifact_store_status = "ok"
    artifact_store_error: str | None = None
    if artifact_store is None:
        try:
            artifact_store = create_artifact_store()
        except (ImportError, OSError, ValueError) as exc:
            artifact_store_status = "error"
            artifact_store_error = str(exc)
    ai_builder_service = AiBuilderService.from_env(store=_default_ai_audit_store(ai_audit_store))
    execution_lane_service = execution_lane_service or ExecutionLaneService()
    llm_config_service = llm_config_service or LlmConfigService()
    runtime_event_service = runtime_event_service or RuntimeEventService()
    from packages.builder_metadata.version import get_canonical_version as _get_canonical_version
    app = FastAPI(title="Nautilus Builder API", version=_get_canonical_version())

    # --- Middleware (added in reverse execution order: last added = first executed) ---

    # Request ID middleware: adds X-Request-ID to every response
    app.add_middleware(RequestIdMiddleware)

    # Audit middleware: logs mutations to audit_events
    _audit_writer = audit_writer or _build_audit_writer(_pg_conn)
    app.add_middleware(AuditMiddleware, audit_writer=_audit_writer)
    app.add_middleware(AuthContextMiddleware, auth_token_service=auth_token_service)

    # --- Rate limiter backend selection ---
    _rate_backend = (os.environ.get("BUILDER_RATE_LIMIT_BACKEND") or "memory").strip().lower()
    if rate_limiter is not None:
        _rate_limiter = rate_limiter
    elif _rate_backend == "redis":
        _redis_url = os.environ.get("BUILDER_REDIS_URL", "redis://localhost:6379/0").strip()
        _rate_limiter = RedisRateLimiter(
            max_requests=int(os.environ.get("BUILDER_RATE_LIMIT", "100")),
            window_seconds=60,
            redis_url=_redis_url,
            fail_closed=_strictest_configured_env() == BuilderEnvironment.PRODUCTION,
        )
    else:
        _rate_limiter = InMemoryRateLimiter(
            max_requests=int(os.environ.get("BUILDER_RATE_LIMIT", "100")),
            window_seconds=60,
        )

    # L8: CORS middleware — configurable via env vars
    try:
        from starlette.middleware.cors import CORSMiddleware
    except ImportError:
        CORSMiddleware = None
    if CORSMiddleware is not None:
        cors_origins = _cors_origins_from_env()
        if cors_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    def require_context(authorization: str | None) -> tuple[UserProjectContext | None, ApiResponse | None]:
        context, auth_error = _context_from_authorization(authorization, auth_token_service)
        if auth_error is not None or context is None:
            return context, auth_error
        if not _rate_limiter.is_allowed(_rate_limit_key(context)):
            return None, ApiResponse(
                {
                    "error": "rate_limited",
                    "details": "API rate limit exceeded for authenticated Builder context",
                },
                status_code=429,
            )
        return context, None

    @app.get("/health")
    def health() -> dict[str, object]:
        return health_payload()

    @app.get("/health/live")
    def health_live() -> dict[str, object]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def health_ready() -> dict[str, object]:
        checks: dict[str, str] = {
            "database": "ok" if _pg_dsn else "not_configured",
            "artifact_store": artifact_store_status,
        }
        if artifact_store_error is not None:
            checks["artifact_store_error"] = artifact_store_error
        return {"ready": artifact_store_status == "ok", "checks": checks}

    @app.get("/health/build")
    def health_build() -> dict[str, object]:
        from packages.builder_metadata.build_info import get_build_info as _get_build_info
        return _get_build_info()

    @app.get("/api/adapters")
    def adapters(authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(ApiResponse(adapters_payload(pg_repo=_pg_adapter_repo)), JSONResponse)

    @app.get("/api/instruments/{adapter_id}/{query}")
    def instruments(adapter_id: str, query: str, authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(instruments_payload(adapter_id, query, pg_repo=_pg_adapter_repo), JSONResponse)

    @app.get("/api/instruments")
    def instruments_query(adapter_id: str, query: str, authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(instruments_payload(adapter_id, query, pg_repo=_pg_adapter_repo), JSONResponse)

    @app.get("/api/data-availability/{adapter_id}/{instrument_id}")
    def data_availability(adapter_id: str, instrument_id: str, authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(data_availability_payload(adapter_id, instrument_id, pg_repo=_pg_adapter_repo), JSONResponse)

    @app.post("/api/backtest-profiles/validate")
    def validate_backtest_profile(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(validate_backtest_profile_payload(payload), JSONResponse)

    @app.post("/api/pipeline/run")
    def run_pipeline_route(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(run_pipeline_payload(payload), JSONResponse)

    @app.post("/api/pipeline/promote")
    def promote_pipeline_route(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(promote_pipeline_payload(payload), JSONResponse)

    @app.post("/api/backtest-jobs")
    def create_backtest_job(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            create_backtest_job_payload(
                backtest_job_service,
                payload,
                context=context,
                dataset_registry=catalog_dataset_registry,
                strict_scope=True,
            ),
            JSONResponse,
        )

    @app.get("/api/backtest-jobs/{job_id}")
    def backtest_job(
        job_id: str,
        authorization: str | None = Header(default=None),
        user_id: str | None = None,
        project_id: str | None = None,
    ) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            backtest_job_payload(
                backtest_job_service,
                job_id,
                context=context,
                user_id=user_id,
                project_id=project_id,
                strict_scope=True,
            ),
            JSONResponse,
        )

    @app.post("/api/backtest-jobs/{job_id}/run")
    def run_backtest_job_route(
        job_id: str,
        payload: dict[str, Any],
        user_id: str | None = None,
        project_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        _ = payload
        return _fastapi_response(
            run_backtest_job_payload(
                backtest_job_service,
                job_id,
                events=runtime_event_service,
                strategy_repository=strategy_repository,
                dataset_registry=catalog_dataset_registry,
                artifact_store=artifact_store,
                context=context,
                user_id=user_id,
                project_id=project_id,
                strict_scope=True,
            ),
            JSONResponse,
        )

    @app.post("/api/backtest-jobs/{job_id}/cancel")
    def cancel_backtest_job(
        job_id: str,
        payload: dict[str, Any],
        user_id: str | None = None,
        project_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            cancel_backtest_job_payload(
                backtest_job_service,
                job_id,
                context=context,
                user_id=user_id,
                project_id=project_id,
                strict_scope=True,
            ),
            JSONResponse,
        )

    @app.get("/api/backtest-jobs/{job_id}/events")
    def backtest_job_events(job_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        scope_check = backtest_job_payload(
            backtest_job_service,
            job_id,
            context=context,
            strict_scope=True,
        )
        if scope_check.status_code != 200:
            return _fastapi_response(scope_check, JSONResponse)
        return _fastapi_response(backtest_job_events_payload(job_id, service=runtime_event_service), JSONResponse)

    @app.get("/api/execution-lane/status")
    def execution_lane_status(runtime_profile_id: str | None = None, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return execution_lane_service.snapshot(runtime_profile_id=runtime_profile_id, project_id=context.project_id)

    @app.get("/api/execution-lane/runtime-plan")
    def execution_lane_runtime_plan(
        runtime_profile_id: str,
        command_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        scope_error = _execution_lane_profile_scope_error(execution_lane_service, runtime_profile_id, context)
        if scope_error is not None:
            return _fastapi_response(scope_error, JSONResponse)
        if command_id is not None:
            command_scope_error = _execution_lane_command_scope_error(execution_lane_service, command_id, context)
            if command_scope_error is not None:
                return _fastapi_response(command_scope_error, JSONResponse)
        return _fastapi_response(
            execution_lane_runtime_plan_payload(
                service=execution_lane_service,
                runtime_profile_id=runtime_profile_id,
                command_id=command_id,
            ),
            JSONResponse,
        )

    @app.get("/api/config/llm")
    def llm_config(authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return get_llm_config_payload(llm_config_service)

    @app.post("/api/config/llm")
    def save_llm_config(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(save_llm_config_payload(llm_config_service, payload, pg_config_repo=_pg_config_repo if _pg_conn else None), JSONResponse)

    @app.post("/api/execution-lane/credential-slots")
    def create_execution_lane_credential_slot(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        if str(payload.get("project_id", "")).strip() != context.project_id:
            return _fastapi_response(
                ApiResponse(
                    {"error": "project_scope_mismatch", "details": "credential slot project_id does not match bearer token scope"},
                    status_code=403,
                ),
                JSONResponse,
            )
        return _fastapi_response(create_execution_lane_credential_slot_payload(payload, service=execution_lane_service), JSONResponse)

    @app.post("/api/execution-lane/profiles")
    def register_execution_lane_profile(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        scope_error = _payload_project_scope_error(payload, context, "runtime profile")
        if scope_error is not None:
            return _fastapi_response(scope_error, JSONResponse)
        return _fastapi_response(register_execution_lane_profile_payload(payload, service=execution_lane_service), JSONResponse)

    @app.post("/api/execution-lane/commands")
    def enqueue_execution_lane_command(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        scope_error = _payload_project_scope_error(payload, context, "execution command")
        if scope_error is not None:
            return _fastapi_response(scope_error, JSONResponse)
        runtime_profile_id = str(payload.get("runtime_profile_id", "")).strip()
        profile_scope_error = _execution_lane_profile_scope_error(execution_lane_service, runtime_profile_id, context)
        if profile_scope_error is not None:
            return _fastapi_response(profile_scope_error, JSONResponse)
        return _fastapi_response(enqueue_execution_lane_command_payload(payload, service=execution_lane_service), JSONResponse)

    @app.post("/api/execution-lane/worker/run-once")
    def execution_lane_worker_run_once(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        runtime_profile_id = str(payload.get("runtime_profile_id", "")).strip()
        profile_scope_error = _execution_lane_profile_scope_error(execution_lane_service, runtime_profile_id, context)
        if profile_scope_error is not None:
            return _fastapi_response(profile_scope_error, JSONResponse)
        return _fastapi_response(run_execution_lane_worker_once_payload(payload, service=execution_lane_service), JSONResponse)

    @app.post("/api/execution-lane/sessions/start")
    def execution_lane_session_start(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        if str(payload.get("project_id", context.project_id)).strip() != context.project_id:
            return _fastapi_response(ApiResponse({"error": "project_scope_mismatch", "details": "session project scope does not match bearer token scope"}, status_code=403), JSONResponse)
        try:
            profile = execution_lane_service.get_profile(str(payload.get("runtime_profile_id", "")).strip())
        except KeyError:
            return _fastapi_response(start_execution_lane_paper_session_payload(payload, service=execution_lane_service), JSONResponse)
        if profile.project_id != context.project_id:
            return _fastapi_response(ApiResponse({"error": "project_scope_mismatch", "details": "session runtime profile project_id does not match bearer token scope"}, status_code=403), JSONResponse)
        command_id = str(payload.get("command_id", "")).strip()
        if command_id:
            command_scope_error = _execution_lane_command_scope_error(execution_lane_service, command_id, context)
            if command_scope_error is not None:
                return _fastapi_response(command_scope_error, JSONResponse)
        return _fastapi_response(start_execution_lane_paper_session_payload(payload, service=execution_lane_service), JSONResponse)

    @app.get("/api/execution-lane/sessions/{session_id}")
    def execution_lane_session_get(session_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        try:
            session = execution_lane_service.get_session(session_id)
        except KeyError:
            return _fastapi_response(execution_lane_session_payload(session_id=session_id, service=execution_lane_service), JSONResponse)
        if session.project_id != context.project_id:
            return _fastapi_response(ApiResponse({"error": "project_scope_mismatch", "details": "session project_id does not match bearer token scope"}, status_code=403), JSONResponse)
        return _fastapi_response(execution_lane_session_payload(session_id=session_id, service=execution_lane_service), JSONResponse)

    @app.post("/api/execution-lane/sessions/{session_id}/stop")
    def execution_lane_session_stop(session_id: str, payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        try:
            session = execution_lane_service.get_session(session_id)
        except KeyError:
            return _fastapi_response(stop_execution_lane_session_payload(session_id=session_id, payload=payload, service=execution_lane_service), JSONResponse)
        if session.project_id != context.project_id:
            return _fastapi_response(ApiResponse({"error": "project_scope_mismatch", "details": "session project_id does not match bearer token scope"}, status_code=403), JSONResponse)
        return _fastapi_response(stop_execution_lane_session_payload(session_id=session_id, payload=payload, service=execution_lane_service), JSONResponse)

    @app.get("/api/runtime-events/replay")
    def runtime_events_replay(
        job_id: str = "bt_001",
        authorization: str | None = Header(default=None),
    ) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(ApiResponse(replay_runtime_events_payload(job_id=job_id)), JSONResponse)

    @app.get("/api/strategy-registry/external")
    def strategy_registry_external(authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(ApiResponse(list_external_strategy_payloads()), JSONResponse)

    @app.post("/api/strategies")
    def create_strategy(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(create_strategy_payload(strategy_repository, payload, context=context), JSONResponse)

    @app.get("/api/strategies")
    def list_strategies(authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(list_strategies_payload(strategy_repository, context=context), JSONResponse)

    @app.get("/api/strategies/{strategy_id}/evidence-summary")
    def strategy_evidence_summary(strategy_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(strategy_evidence_summary_payload(strategy_repository, strategy_id, backtest_job_service=backtest_job_service, context=context), JSONResponse)

    @app.get("/api/strategies/{strategy_id}")
    def strategy_detail(strategy_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(strategy_detail_payload(strategy_repository, strategy_id, context=context), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/draft")
    def update_strategy_draft(strategy_id: str, payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(update_strategy_draft_payload(strategy_repository, strategy_id, payload, context=context), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/versions")
    def create_strategy_version(strategy_id: str, payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(create_strategy_version_payload(strategy_repository, strategy_id, payload, context=context), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/approve")
    def approve_strategy(strategy_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        try:
            result = strategy_repository.approve_strategy(strategy_id, context=context)
        except ProjectScopeError as exc:
            return _fastapi_response(ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403), JSONResponse)
        if result is None:
            return _fastapi_response(ApiResponse({"error": "strategy_not_found_or_not_promotable", "strategy_id": strategy_id}, status_code=422), JSONResponse)
        return _fastapi_response(ApiResponse(result), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/clone")
    def clone_strategy(strategy_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        try:
            result = strategy_repository.clone_strategy(strategy_id, context=context)
        except ProjectScopeError as exc:
            return _fastapi_response(ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403), JSONResponse)
        if result is None:
            return _fastapi_response(ApiResponse({"error": "strategy_not_found", "strategy_id": strategy_id}, status_code=404), JSONResponse)
        return _fastapi_response(ApiResponse(result, status_code=201), JSONResponse)

    @app.post("/api/ai-builder/draft")
    def ai_builder_draft(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(ApiResponse(generate_ai_draft_payload(str(payload.get("prompt", "")), service=ai_builder_service)), JSONResponse)

    @app.post("/api/ai-builder/apply")
    def ai_builder_apply(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(apply_ai_draft_payload(payload, service=ai_builder_service), JSONResponse)

    @app.post("/api/promotions/shadow")
    def promotions_shadow(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            create_shadow_payload(
                payload,
                context=context,
                artifact_store=artifact_store,
                strict_evidence=True,
            ),
            JSONResponse,
        )

    @app.post("/api/promotions/request")
    def promotions_request(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> Any:
        _context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(request_promotion_payload(payload), JSONResponse)

    @app.get("/api/workflow/results/{result_id}")
    def workflow_result(result_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            workflow_result_payload(
                workflow_repository,
                result_id,
                context=context,
                allow_fixture_fallback=False,
            ),
            JSONResponse,
        )

    @app.get("/api/results")
    def list_results(limit: int | None = None, offset: int = 0, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            list_results_payload(workflow_repository, limit=limit, offset=offset, context=context),
            JSONResponse,
        )

    @app.get("/api/results/{result_id}")
    def result_dashboard(result_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            workflow_result_payload(
                workflow_repository,
                result_id,
                context=context,
                allow_fixture_fallback=False,
            ),
            JSONResponse,
        )

    @app.get("/api/workflow/results/{result_id}/suggestions")
    def workflow_result_suggestions(result_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(workflow_result_suggestions_payload(workflow_repository, result_id, context=context), JSONResponse)

    @app.get("/api/workflow/lineages/{strategy_lineage_id}/status")
    def workflow_lineage_status(strategy_lineage_id: str, authorization: str | None = Header(default=None)) -> Any:
        context, auth_error = require_context(authorization)
        if auth_error is not None:
            return _fastapi_response(auth_error, JSONResponse)
        return _fastapi_response(
            workflow_lineage_status_payload(workflow_repository, strategy_lineage_id, context=context),
            JSONResponse,
        )

    return app


def _payload_project_scope_error(
    payload: dict[str, Any],
    context: UserProjectContext,
    resource_name: str,
) -> ApiResponse | None:
    payload_project_id = str(payload.get("project_id", "")).strip()
    if payload_project_id == context.project_id:
        return None
    return ApiResponse(
        {
            "error": "project_scope_mismatch",
            "details": f"{resource_name} project_id does not match bearer token scope",
        },
        status_code=403,
    )


def _execution_lane_profile_scope_error(
    service: ExecutionLaneService,
    runtime_profile_id: str,
    context: UserProjectContext,
) -> ApiResponse | None:
    if not runtime_profile_id:
        return None
    try:
        service.get_profile(runtime_profile_id, project_id=context.project_id)
    except ProjectScopeError:
        return ApiResponse(
            {
                "error": "project_scope_mismatch",
                "details": "runtime profile project_id does not match bearer token scope",
            },
            status_code=403,
        )
    except KeyError:
        return None
    return None


def _execution_lane_command_scope_error(
    service: ExecutionLaneService,
    command_id: str,
    context: UserProjectContext,
) -> ApiResponse | None:
    if not command_id:
        return None
    try:
        service.get_command(command_id, project_id=context.project_id)
    except ProjectScopeError:
        return ApiResponse(
            {
                "error": "project_scope_mismatch",
                "details": "execution command project_id does not match bearer token scope",
            },
            status_code=403,
        )
    except KeyError:
        return None
    return None


def _fastapi_payload(response: ApiResponse) -> Any:
    return response.json()


def _fastapi_response(response: ApiResponse, response_class: Any) -> Any:
    return response_class(content=response.json(), status_code=response.status_code)


def _context_from_authorization(
    authorization: str | None,
    auth_token_service: AuthTokenService,
) -> tuple[UserProjectContext | None, ApiResponse | None]:
    if not authorization:
        return None, ApiResponse({"error": "auth_required", "details": "Bearer token is required"}, status_code=401)
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None, ApiResponse({"error": "invalid_auth_token", "details": "Bearer token is required"}, status_code=401)
    try:
        return auth_token_service.verify_token(token.strip()), None
    except InvalidAuthTokenError as exc:
        return None, ApiResponse({"error": "invalid_auth_token", "details": str(exc)}, status_code=401)


def _rate_limit_key(context: UserProjectContext) -> str:
    return f"{context.user_id}:{context.project_id}"


_UNSAFE_DEV_TOKENS = {"dev-token", "test-token", "changeme"}


def _cors_origins_from_env() -> list[str]:
    return [
        origin.strip()
        for origin in os.environ.get("BUILDER_CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]


def _validate_startup_policy() -> None:
    env = _strictest_configured_env()
    validate_production_token(
        env=env,
        token=os.environ.get("BUILDER_API_TOKEN"),
        public_token=os.environ.get("NEXT_PUBLIC_BUILDER_API_TOKEN"),
    )
    validate_cors_config(env=env, origins=_cors_origins_from_env())
    validate_rate_limit_config(
        env=env,
        backend=os.environ.get("BUILDER_RATE_LIMIT_BACKEND"),
        redis_url=os.environ.get("BUILDER_REDIS_URL"),
    )


def _strictest_configured_env() -> BuilderEnvironment:
    configured = [
        validate_builder_env(raw)
        for raw in (
            os.environ.get("BUILDER_ENV", ""),
            os.environ.get("APP_ENV", ""),
        )
        if raw.strip()
    ]
    if not configured:
        return BuilderEnvironment.LOCAL
    priority = {
        BuilderEnvironment.LOCAL: 0,
        BuilderEnvironment.STAGING: 1,
        BuilderEnvironment.PRODUCTION: 2,
    }
    return max(configured, key=lambda env: priority[env])


def _env_user_project_context() -> UserProjectContext:
    return UserProjectContext(
        user_id=os.environ.get("BUILDER_DEV_USER_ID", "local_user"),
        project_id=os.environ.get("BUILDER_DEV_PROJECT_ID", "local_project"),
        role=os.environ.get("BUILDER_DEV_ROLE", "builder"),
    )


def _register_env_dev_token(auth_token_service: AuthTokenService) -> None:
    dev_auth_token = os.environ.get("BUILDER_DEV_AUTH_TOKEN")
    token = (dev_auth_token or os.environ.get("BUILDER_API_TOKEN") or "").strip()
    if not token:
        return
    environment = _strictest_configured_env()
    if environment != BuilderEnvironment.LOCAL and dev_auth_token is not None:
        raise ValueError(
            f"Refusing BUILDER_DEV_AUTH_TOKEN '{token}' in {environment.value} environment. "
            "Use BUILDER_API_TOKEN for staging/production server-side auth."
        )
    if environment != BuilderEnvironment.LOCAL and token in _UNSAFE_DEV_TOKENS:
        raise ValueError(
            f"Refusing to register known dev token '{token}' in {environment.value} environment. "
            "Set BUILDER_API_TOKEN to a strong secret."
        )
    auth_token_service.register_token(
        token=token,
        user_id=os.environ.get("BUILDER_DEV_USER_ID", "local_user"),
        project_id=os.environ.get("BUILDER_DEV_PROJECT_ID", "local_project"),
        role=os.environ.get("BUILDER_DEV_ROLE", "builder"),
    )


def _default_ai_audit_store(ai_audit_store: DraftAuditStoreProtocol | None) -> DraftAuditStoreProtocol:
    if ai_audit_store is not None:
        return ai_audit_store
    sqlite_path = os.environ.get("BUILDER_AI_AUDIT_SQLITE_PATH", "").strip()
    if sqlite_path:
        return SqliteAiDraftAuditStore(connection=sqlite3.connect(sqlite_path))
    environment = _strictest_configured_env()
    if environment == BuilderEnvironment.PRODUCTION:
        raise ValueError("durable AI audit store is required in production")
    return RecordedAiDraftStore()


def _build_audit_writer(pg_conn: Any) -> Any:
    """Build an audit writer function.

    When Postgres is configured, writes audit events to the audit_events table.
    Otherwise, logs to stdout.
    """
    import logging

    _log = logging.getLogger(__name__)

    if pg_conn is not None:
        def _pg_audit_writer(event: dict) -> None:
            try:
                pg_conn.execute(
                    """INSERT INTO builder.audit_events
                       (request_id, actor_id, project_id, action, resource_type, resource_id, status, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        event.get("request_id"),
                        event.get("actor_id") or "unauthenticated",
                        event.get("project_id") or "unknown",
                        event.get("action", event.get("method", "unknown")),
                        event.get("resource_type", "unknown"),
                        event.get("resource_id"),
                        "success" if 200 <= event.get("status_code", 500) < 400 else "failed",
                        event.get("created_at"),
                    ),
                )
            except Exception as exc:
                _log.error("audit_pg_write_failed error=%s event=%s", exc, event.get("request_id"))
                raise

        return _pg_audit_writer

    def _log_audit_writer(event: dict) -> None:
        _log.info(
            "audit_event request_id=%s method=%s route=%s status=%s actor=%s",
            event.get("request_id"),
            event.get("method"),
            event.get("route"),
            event.get("status_code"),
            event.get("actor_id"),
        )

    return _log_audit_writer
