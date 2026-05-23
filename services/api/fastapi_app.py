from __future__ import annotations

from typing import Any

from packages.strategy_spec.repository import InMemoryStrategyRepository
from packages.backtest_jobs.service import BacktestJobService
from packages.workflow_spine import InMemoryWorkflowRepository
from services.api.app import _create_shadow_promotion, _generate_ai_draft
from services.api.routes.backtest_jobs import backtest_job_events_payload, backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload
from services.api.router import ApiResponse
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.promotions import request_promotion_payload
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
):
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
    strategy_repository = strategy_repository or InMemoryStrategyRepository()
    backtest_job_service = backtest_job_service or BacktestJobService()
    app = FastAPI(title="Nautilus Builder API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, object]:
        return health_payload()

    @app.get("/api/adapters")
    def adapters() -> list[dict[str, object]]:
        return adapters_payload()

    @app.get("/api/instruments/{adapter_id}/{query}")
    def instruments(adapter_id: str, query: str) -> Any:
        return instruments_payload(adapter_id, query).json()

    @app.get("/api/instruments")
    def instruments_query(adapter_id: str, query: str) -> Any:
        return instruments_payload(adapter_id, query).json()

    @app.get("/api/data-availability/{adapter_id}/{instrument_id}")
    def data_availability(adapter_id: str, instrument_id: str) -> Any:
        return data_availability_payload(adapter_id, instrument_id).json()

    @app.post("/api/backtest-profiles/validate")
    def validate_backtest_profile(payload: dict[str, Any]) -> Any:
        return _fastapi_response(validate_backtest_profile_payload(payload), JSONResponse)

    @app.post("/api/backtest-jobs")
    def create_backtest_job(payload: dict[str, Any]) -> Any:
        return _fastapi_response(create_backtest_job_payload(backtest_job_service, payload), JSONResponse)

    @app.get("/api/backtest-jobs/{job_id}")
    def backtest_job(job_id: str) -> Any:
        return _fastapi_response(backtest_job_payload(backtest_job_service, job_id), JSONResponse)

    @app.post("/api/backtest-jobs/{job_id}/cancel")
    def cancel_backtest_job(job_id: str, payload: dict[str, Any]) -> Any:
        return _fastapi_response(cancel_backtest_job_payload(backtest_job_service, job_id), JSONResponse)

    @app.get("/api/backtest-jobs/{job_id}/events")
    def backtest_job_events(job_id: str) -> Any:
        return _fastapi_response(backtest_job_events_payload(job_id), JSONResponse)

    @app.get("/api/runtime-events/replay")
    def runtime_events_replay() -> list[dict[str, object]]:
        return replay_runtime_events_payload()

    @app.get("/api/strategy-registry/external")
    def strategy_registry_external() -> list[dict[str, object]]:
        return list_external_strategy_payloads()

    @app.post("/api/strategies")
    def create_strategy(payload: dict[str, Any]) -> Any:
        return _fastapi_response(create_strategy_payload(strategy_repository, payload), JSONResponse)

    @app.get("/api/strategies")
    def list_strategies() -> list[dict[str, object]]:
        return list_strategies_payload(strategy_repository)

    @app.get("/api/strategies/{strategy_id}")
    def strategy_detail(strategy_id: str) -> Any:
        return _fastapi_response(strategy_detail_payload(strategy_repository, strategy_id), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/draft")
    def update_strategy_draft(strategy_id: str, payload: dict[str, Any]) -> Any:
        return _fastapi_response(update_strategy_draft_payload(strategy_repository, strategy_id, payload), JSONResponse)

    @app.post("/api/strategies/{strategy_id}/versions")
    def create_strategy_version(strategy_id: str, payload: dict[str, Any]) -> Any:
        return _fastapi_response(create_strategy_version_payload(strategy_repository, strategy_id, payload), JSONResponse)

    @app.post("/api/ai-builder/draft")
    def ai_builder_draft(payload: dict[str, Any]) -> dict[str, object]:
        return _generate_ai_draft(payload)

    @app.post("/api/promotions/shadow")
    def promotions_shadow(payload: dict[str, Any]) -> dict[str, object]:
        return _create_shadow_promotion(payload)

    @app.post("/api/promotions/request")
    def promotions_request(payload: dict[str, Any]) -> Any:
        return _fastapi_response(request_promotion_payload(payload), JSONResponse)

    @app.get("/api/workflow/results/{result_id}")
    def workflow_result(result_id: str) -> Any:
        response = workflow_result_payload(workflow_repository, result_id)
        return response.json()

    @app.get("/api/results/{result_id}")
    def result_dashboard(result_id: str) -> Any:
        response = workflow_result_payload(workflow_repository, result_id)
        return response.json()

    @app.get("/api/workflow/results/{result_id}/suggestions")
    def workflow_result_suggestions(result_id: str) -> Any:
        response = workflow_result_suggestions_payload(workflow_repository, result_id)
        return response.json()

    @app.get("/api/workflow/lineages/{strategy_lineage_id}/status")
    def workflow_lineage_status(strategy_lineage_id: str) -> Any:
        response = workflow_lineage_status_payload(workflow_repository, strategy_lineage_id)
        return response.json()

    return app


def _fastapi_payload(response: ApiResponse) -> Any:
    return response.json()


def _fastapi_response(response: ApiResponse, response_class: Any) -> Any:
    return response_class(content=response.json(), status_code=response.status_code)
