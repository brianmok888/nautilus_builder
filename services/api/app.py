from services.api.router import ApiApp
from services.api.routes.ai_builder import apply_ai_draft_payload, generate_ai_draft_payload
from services.api.routes.backtest_jobs import backtest_job_events_payload, backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload
from services.api.routes.backtest_execution import run_backtest_job_payload
from services.api.routes.execution_lane import enqueue_execution_lane_command_payload, execution_lane_runtime_plan_payload, execution_lane_status_payload, register_execution_lane_profile_payload
from services.api.routes.health import health_payload
from services.api.routes.market_catalog import adapters_payload, data_availability_payload, instruments_payload, validate_backtest_profile_payload
from services.api.routes.llm_config import get_llm_config_payload, save_llm_config_payload
from services.api.routes.promotions import create_shadow_payload, request_promotion_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads
from services.api.routes.strategies import create_strategy_payload, create_strategy_version_payload, list_strategies_payload, strategy_detail_payload, update_strategy_draft_payload
from services.api.routes.workflow_results import workflow_lineage_status_payload, workflow_result_payload, workflow_result_suggestions_payload
from packages.workflow_spine import InMemoryWorkflowRepository
from packages.artifact_store import LocalJsonArtifactStore
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDatasetRegistryService
from packages.execution_lane import ExecutionLaneService
from packages.llm_config import LlmConfigService
from packages.runtime_events.service import RuntimeEventService
from packages.strategy_spec.repository import InMemoryStrategyRepository


def create_app(
    workflow_repository: InMemoryWorkflowRepository | None = None,
    strategy_repository: InMemoryStrategyRepository | None = None,
    backtest_job_service: BacktestJobService | None = None,
    execution_lane_service: ExecutionLaneService | None = None,
    llm_config_service: LlmConfigService | None = None,
    catalog_dataset_registry: CatalogDatasetRegistryService | None = None,
    artifact_store: LocalJsonArtifactStore | None = None,
    runtime_event_service: RuntimeEventService | None = None,
) -> ApiApp:
    workflow_repository = workflow_repository or InMemoryWorkflowRepository()
    strategy_repository = strategy_repository or InMemoryStrategyRepository()
    backtest_job_service = backtest_job_service or BacktestJobService()
    execution_lane_service = execution_lane_service or ExecutionLaneService()
    llm_config_service = llm_config_service or LlmConfigService()
    runtime_event_service = runtime_event_service or RuntimeEventService()
    app = ApiApp()
    app.route("GET", "/health", health_payload)
    app.route("GET", "/api/adapters", adapters_payload)
    app.route("GET", "/api/instruments", instruments_payload)
    app.route("GET", "/api/instruments/{adapter_id}/{query}", instruments_payload)
    app.route("GET", "/api/data-availability/{adapter_id}/{instrument_id}", data_availability_payload)
    app.route("POST", "/api/backtest-profiles/validate", validate_backtest_profile_payload)
    app.route("POST", "/api/backtest-jobs", lambda payload: create_backtest_job_payload(backtest_job_service, payload))
    app.route("GET", "/api/backtest-jobs/{job_id}", lambda job_id, user_id=None, project_id=None: backtest_job_payload(backtest_job_service, job_id, user_id=user_id, project_id=project_id))
    app.route("POST", "/api/backtest-jobs/{job_id}/cancel", lambda job_id, payload, user_id=None, project_id=None: cancel_backtest_job_payload(backtest_job_service, job_id, user_id=user_id, project_id=project_id))
    app.route(
        "POST",
        "/api/backtest-jobs/{job_id}/run",
        lambda job_id, payload, user_id=None, project_id=None: run_backtest_job_payload(
            backtest_job_service,
            job_id,
            events=runtime_event_service,
            strategy_repository=strategy_repository,
            dataset_registry=catalog_dataset_registry,
            artifact_store=artifact_store,
            user_id=user_id,
            project_id=project_id,
        ),
    )
    app.route("GET", "/api/backtest-jobs/{job_id}/events", lambda job_id: backtest_job_events_payload(job_id, service=runtime_event_service))
    app.route("POST", "/api/strategies", lambda payload: create_strategy_payload(strategy_repository, payload))
    app.route("GET", "/api/strategies", lambda: list_strategies_payload(strategy_repository))
    app.route("GET", "/api/strategies/{strategy_id}", lambda strategy_id: strategy_detail_payload(strategy_repository, strategy_id))
    app.route("POST", "/api/strategies/{strategy_id}/draft", lambda strategy_id, payload: update_strategy_draft_payload(strategy_repository, strategy_id, payload))
    app.route("POST", "/api/strategies/{strategy_id}/versions", lambda strategy_id, payload: create_strategy_version_payload(strategy_repository, strategy_id, payload))
    app.route("GET", "/api/runtime-events/replay", replay_runtime_events_payload)
    app.route("GET", "/api/execution-lane/status", lambda runtime_profile_id=None: execution_lane_status_payload(service=execution_lane_service, runtime_profile_id=runtime_profile_id))
    app.route(
        "GET",
        "/api/execution-lane/runtime-plan",
        lambda runtime_profile_id, command_id=None: execution_lane_runtime_plan_payload(
            service=execution_lane_service,
            runtime_profile_id=runtime_profile_id,
            command_id=command_id,
        ),
    )
    app.route("GET", "/api/config/llm", lambda: get_llm_config_payload(llm_config_service))
    app.route("POST", "/api/config/llm", lambda payload: save_llm_config_payload(llm_config_service, payload))
    app.route("POST", "/api/execution-lane/profiles", lambda payload: register_execution_lane_profile_payload(payload, service=execution_lane_service))
    app.route("POST", "/api/execution-lane/commands", lambda payload: enqueue_execution_lane_command_payload(payload, service=execution_lane_service))
    app.route("GET", "/api/strategy-registry/external", list_external_strategy_payloads)
    app.route("POST", "/api/ai-builder/draft", _generate_ai_draft)
    app.route("POST", "/api/ai-builder/apply", apply_ai_draft_payload)
    app.route("POST", "/api/promotions/shadow", create_shadow_payload)
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
