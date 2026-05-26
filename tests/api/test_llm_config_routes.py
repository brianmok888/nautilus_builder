from services.api.app import create_app


def test_llm_config_routes_load_and_save_non_secret_openai_compatible_settings():
    app = create_app()

    default_response = app.get("/api/config/llm")

    assert default_response.status_code == 200
    default_payload = default_response.json()
    assert default_payload["provider_type"] == "openai-compatible"
    assert default_payload["credential_inputs_allowed"] is False
    assert "api_key" not in str(default_payload).lower()

    save_response = app.post(
        "/api/config/llm",
        json={
            "provider_type": "local-openai-compatible",
            "base_url": "http://127.0.0.1:11434/v1",
            "draft_model": "qwen-strategy-draft",
            "validation_model": "qwen-strategy-validate",
            "explanation_model": "qwen-strategy-explain",
        },
    )

    assert save_response.status_code == 200
    saved_payload = save_response.json()
    assert saved_payload["base_url"] == "http://127.0.0.1:11434/v1"
    assert saved_payload["roles"]["draft_strategy_spec"] == "qwen-strategy-draft"
    assert saved_payload["secrets_storage"] == "server_environment"


def test_llm_config_rejects_browser_secret_fields():
    app = create_app()

    response = app.post(
        "/api/config/llm",
        json={
            "provider_type": "openai-compatible",
            "base_url": "https://api.openai.com/v1",
            "draft_model": "strategy-draft-model",
            "validation_model": "strategy-draft-model",
            "explanation_model": "strategy-draft-model",
            "api_key": "sk-not-allowed-in-browser-config",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_llm_config"
