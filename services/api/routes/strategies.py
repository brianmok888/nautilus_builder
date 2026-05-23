from __future__ import annotations

from packages.strategy_spec.models import StrategySpec
from packages.strategy_spec.repository import InMemoryStrategyRepository
from services.api.router import ApiResponse


def create_strategy_payload(repository: InMemoryStrategyRepository, payload: dict[str, object]) -> ApiResponse:
    record = repository.save(StrategySpec.model_validate(payload))
    return ApiResponse(record, status_code=201)


def list_strategies_payload(repository: InMemoryStrategyRepository) -> list[dict[str, object]]:
    return repository.list()


def strategy_detail_payload(repository: InMemoryStrategyRepository, strategy_id: str) -> ApiResponse:
    record = repository.detail(strategy_id)
    if record is None:
        return ApiResponse({"error": "strategy_not_found", "strategy_id": strategy_id}, status_code=404)
    return ApiResponse(record)


def update_strategy_draft_payload(repository: InMemoryStrategyRepository, strategy_id: str, payload: dict[str, object]) -> ApiResponse:
    record = repository.update_draft(strategy_id, StrategySpec.model_validate(payload))
    if record is None:
        return ApiResponse({"error": "strategy_not_found", "strategy_id": strategy_id}, status_code=404)
    return ApiResponse(record)


def create_strategy_version_payload(repository: InMemoryStrategyRepository, strategy_id: str, payload: dict[str, object]) -> ApiResponse:
    record = repository.create_version(strategy_id, StrategySpec.model_validate(payload))
    if record is None:
        return ApiResponse({"error": "strategy_not_found", "strategy_id": strategy_id}, status_code=404)
    return ApiResponse(record, status_code=201)
