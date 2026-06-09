from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unwrap(response):
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "ok"
    return payload["data"]


def test_supermap_config_contract():
    config = unwrap(client.get("/api/supermap/config"))
    assert "iserver" in config
    assert "services" in config
    assert "scene" in config["services"]
    assert "layers" in config
    assert config["_meta"]["using_local_config"] in {True, False}

    services = unwrap(client.get("/api/supermap/services"))
    assert isinstance(services, list)
    assert all({"id", "name", "url", "type", "status"} <= set(service) for service in services)

    status = unwrap(client.get("/api/supermap/status"))
    assert "services" in status
    assert "map" in status
    assert "data" in status
    assert "layers" in status
    assert isinstance(status["layers"], list)


def test_validation_error_contract():
    response = client.post(
        "/api/vision/match",
        json={
            "task_id": "task_001",
            "image_id": "demo_uav_001",
            "top_k": 0,
            "algorithm_mode": "precomputed",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["errors"]
    assert "request validation failed" in payload["message"]
