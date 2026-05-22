from services.api.router import ApiApp
from services.api.routes.ai_builder import generate_ai_draft_payload
from services.api.routes.health import health_payload
from services.api.routes.promotions import create_shadow_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.api.routes.strategy_registry import list_external_strategy_payloads


def create_app() -> ApiApp:
    app = ApiApp()
    app.route("GET", "/health", health_payload)
    app.route("GET", "/api/runtime-events/replay", replay_runtime_events_payload)
    app.route("GET", "/api/strategy-registry/external", list_external_strategy_payloads)
    app.route("POST", "/api/ai-builder/draft", _generate_ai_draft)
    app.route("POST", "/api/promotions/shadow", _create_shadow_promotion)
    return app


def _generate_ai_draft(payload: dict[str, object]) -> dict[str, object]:
    return generate_ai_draft_payload(str(payload.get("prompt", "")))


def _create_shadow_promotion(payload: dict[str, object]) -> dict[str, object]:
    return create_shadow_payload(
        strategy_version=str(payload.get("strategy_version", "")),
        compile_hash=str(payload.get("compile_hash", "")),
    )
