from __future__ import annotations

from typing import Any

from packages.ai_builder.provider import DraftAuditStoreProtocol, RecordedAiDraftStore
from packages.ai_builder.service import AiBuilderService
from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import AuthTokenService, InvalidAuthTokenError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDatasetRegistryService
from packages.strategy_spec.repository import InMemoryStrategyRepository
from packages.workflow_spine import InMemoryWorkflowRepository
from services.api.routes.ai_builder import apply_ai_draft_payload, generate_ai_draft_payload
from services.api.routes.backtest_jobs import backtest_job_events_payload, backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload
from services.api.router import ApiResponse
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.promotions import create_shadow_payload, request_promotion_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads
from services.api.routes.strategies import create_strategy_payload, create_strategy_version_payload, list_strategies_payload, strategy_detail_payload, update_strategy_draft_payload
from services.api.routes.workflow_results import (
    workflow_lineage_status_payload,
    workflow_result_payload,
    workflow_result_suggestions_payload,
)


def create_fastapi_app(
    workflow_repository: InMemoryWorkflowRepository | None = None,
    strategy_repository: InMemoryStrategyRepository | None = None,
    backtest_job_service: BacktestJobService | None = None,
    auth_token_service: AuthTokenService | None = None,
    catalog_dataset_registry: CatalogDatasetRegistryService | None = None,
    artifact_store: LocalJsonArtifactStore | None = None,
    ai_audit_store: DraftAuditStoreProtocol | None = None,
):
    from fastapi import FastAPI, Header
    from fastapi.responses import JSONResponse

    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
    strategy_repository = strategy_repository or InMemoryStrategyRepository()
    backtest_job_service = backtest_job_service or BacktestJobService()
    auth_token_service = auth_token_service or AuthTokenService()
    catalog_dataset_registry = catalog_dataset_registry or CatalogDatasetRegistryService()
    ai_builder_service = AiBuilderService.from_env(store=ai_audit_store or RecordedAiDraftStore())
    app = FastAPI(title="Nautilus Builder API", version="0.1.0")

    def require_context(authorization: str | None) -> tuple[UserProjectContext | None, ApiResponse | None]:
        return _context_from_authorization(authorization, auth_token_service)

    @app.get("/health")
    def health() -> dict[str, object]:
        return health_payload()

    @app.get("/api/adapters")
    def adapters() -> list[dict[str, object]]:
        return adapters_payload()

    @app.get("/api/instruments/{adapter_id}/{query}")
    def instruments(adapter_id: str, query: str) -> Any:
        return _fastapi_response(instruments_payload(adapter_id, query), JSONResponse)

    @app.get("/api/instruments")
    def instruments_query(adapter_id: str, query: str) -> Any:
        return _fastapi_response(instruments_payload(adapter_id, query), JSONResponse)

    @app.get("/api/data-availability/{adapter_id}/{instrument_id}")
    def data_availability(adapter_id: str, instrument_id: str) -> Any:
        return _fastapi_response(data_availability_payload(adapter_id, instrument_id), JSONResponse)

    @app.post("/api/backtest-profiles/validate")
    def validate_backtest_profile(payload: dict[str, Any]) -> Any:
        return _fastapi_response(validate_backtest_profile_payload(payload), JSONResponse)

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
        user_id: str | None = None,
        project_id: str | None = None,
        authorization: str | None = Header(default=None),
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
    def backtest_job_events(job_id: str) -> Any:
        return _fastapi_response(backtest_job_events_payload(job_id), JSONResponse)

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
    def strategy_registry_external() -> list[dict[str, object]]:
        return list_external_strategy_payloads()

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
