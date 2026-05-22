from services.api.app import create_app


def test_health_endpoint_reports_api_ready() -> None:
    app = create_app()

    response = app.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "nautilus_builder_api",
    }
