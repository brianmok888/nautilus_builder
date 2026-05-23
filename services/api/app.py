from services.api.router import ApiApp
from services.api.routes.ai_builder import generate_ai_draft_payload
from services.api.routes.backtest_jobs import backtest_job_events_payload, backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.promotions import create_shadow_payload, request_promotion_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads
from services.api.routes.strategies import create_strategy_payload, create_strategy_version_payload, list_strategies_payload, strategy_detail_payload, update_strategy_draft_payload
from services.api.routes.workflow_results import workflow_lineage_status_payload, workflow_result_payload, workflow_result_suggestions_payload
from packages.workflow_spine import InMemoryWorkflowRepository
from packages.backtest_jobs.service import BacktestJobService
from packages.strategy_spec.repository import InMemoryStrategyRepository


def create_app(
    workflow_repository: InMemoryWorkflowRepository | None = None,
    strategy_repository: InMemoryStrategyRepository | None = None,
    backtest_job_service: BacktestJobService | None = None,
) -> ApiApp:
    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
    strategy_repository = strategy_repository or InMemoryStrategyRepository()
    backtest_job_service = backtest_job_service or BacktestJobService()
    app = ApiApp()
    app.route("GET", "/health", health_payload)
    app.route("GET", "/api/adapters", adapters_payload)
    app.route("GET", "/api/instruments", instruments_payload)
    app.route("GET", "/api/instruments/{adapter_id}/{query}", instruments_payload)
    app.route("GET", "/api/data-availability/{adapter_id}/{instrument_id}", data_availability_payload)
    app.route("POST", "/api/backtest-profiles/validate", validate_backtest_profile_payload)
    app.route("POST", "/api/backtest-jobs", lambda payload: create_backtest_job_payload(backtest_job_service, payload))
    app.route("GET", "/api/backtest-jobs/{job_id}", lambda job_id: backtest_job_payload(backtest_job_service, job_id))
    app.route("POST", "/api/backtest-jobs/{job_id}/cancel", lambda job_id, payload: cancel_backtest_job_payload(backtest_job_service, job_id))
    app.route("GET", "/api/backtest-jobs/{job_id}/events", backtest_job_events_payload)
    app.route("POST", "/api/strategies", lambda payload: create_strategy_payload(strategy_repository, payload))
    app.route("GET", "/api/strategies", lambda: list_strategies_payload(strategy_repository))
    app.route("GET", "/api/strategies/{strategy_id}", lambda strategy_id: strategy_detail_payload(strategy_repository, strategy_id))
    app.route("POST", "/api/strategies/{strategy_id}/draft", lambda strategy_id, payload: update_strategy_draft_payload(strategy_repository, strategy_id, payload))
    app.route("POST", "/api/strategies/{strategy_id}/versions", lambda strategy_id, payload: create_strategy_version_payload(strategy_repository, strategy_id, payload))
    app.route("GET", "/api/runtime-events/replay", replay_runtime_events_payload)
    app.route("GET", "/api/strategy-registry/external", list_external_strategy_payloads)
    app.route("POST", "/api/ai-builder/draft", _generate_ai_draft)
    app.route("POST", "/api/promotions/shadow", _create_shadow_promotion)
    app.route("POST", "/api/promotions/request", request_promotion_payload)
    app.route("GET", "/api/workflow/results/{result_id}", lambda result_id: workflow_result_payload(workflow_repository, result_id))
    app.route("GET", "/api/results/{result_id}", lambda result_id: workflow_result_payload(workflow_repository, result_id))
    app.route(
        "GET",
        "/api/workflow/results/{result_id}/suggestions",
        lambda result_id: workflow_result_suggestions_payload(workflow_repository, result_id),
    )
    app.route(
        "GET",
        "/api/workflow/lineages/{strategy_lineage_id}/status",
        lambda strategy_lineage_id: workflow_lineage_status_payload(workflow_repository, strategy_lineage_id),
    )
    return app


def _generate_ai_draft(payload: dict[str, object]) -> dict[str, object]:
    return generate_ai_draft_payload(str(payload.get("prompt", "")))


def _create_shadow_promotion(payload: dict[str, object]) -> dict[str, object]:
    return create_shadow_payload(
        strategy_version=str(payload.get("strategy_version", "")),
        compile_hash=str(payload.get("compile_hash", "")),
    )
