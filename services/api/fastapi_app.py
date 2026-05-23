from __future__ import annotations

from typing import Any

from packages.workflow_spine import InMemoryWorkflowRepository
from services.api.app import _create_shadow_promotion, _generate_ai_draft
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads
from services.api.routes.workflow_results import (
    workflow_lineage_status_payload,
    workflow_result_payload,
    workflow_result_suggestions_payload,
)


def create_fastapi_app(workflow_repository: InMemoryWorkflowRepository | None = None):
    from fastapi import FastAPI

    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
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

    @app.get("/api/data-availability/{adapter_id}/{instrument_id}")
    def data_availability(adapter_id: str, instrument_id: str) -> Any:
        return data_availability_payload(adapter_id, instrument_id).json()

    @app.post("/api/backtest-profiles/validate")
    def validate_backtest_profile(payload: dict[str, Any]) -> Any:
        return validate_backtest_profile_payload(payload).json()

    @app.get("/api/runtime-events/replay")
    def runtime_events_replay() -> list[dict[str, object]]:
        return replay_runtime_events_payload()

    @app.get("/api/strategy-registry/external")
    def strategy_registry_external() -> list[dict[str, object]]:
        return list_external_strategy_payloads()

    @app.post("/api/ai-builder/draft")
    def ai_builder_draft(payload: dict[str, Any]) -> dict[str, object]:
        return _generate_ai_draft(payload)

    @app.post("/api/promotions/shadow")
    def promotions_shadow(payload: dict[str, Any]) -> dict[str, object]:
        return _create_shadow_promotion(payload)

    @app.get("/api/workflow/results/{result_id}")
    def workflow_result(result_id: str) -> Any:
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
