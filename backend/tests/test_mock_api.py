from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unwrap(response):
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "ok"
    return payload["data"]


def test_health_contract():
    data = unwrap(client.get("/api/health"))
    assert data == {"status": "ok"}


def test_route_plan_and_risk_analysis_contract():
    tasks = unwrap(client.get("/api/tasks"))
    task = unwrap(client.get(f"/api/tasks/{tasks[0]['id']}"))["task"]

    routes = unwrap(
        client.post(
            "/api/routes/plan",
            json={
                "task_id": task["id"],
                "start": task["start"],
                "target": task["target"],
                "modes": ["shortest", "safest", "balanced"],
            },
        )
    )
    assert [route["mode"] for route in routes] == ["shortest", "safest", "balanced"]
    assert all(route["points"][0] == task["start"] for route in routes)
    assert all(route["points"][-1] == task["target"] for route in routes)

    risk = unwrap(client.post("/api/risks/analyze", json={"task_id": task["id"], "route": routes[0]}))
    assert 0 <= risk["score"] <= 100
    assert risk["profile"]
    assert "stats" in risk


def test_simulation_replan_and_report_contract():
    task = unwrap(client.get("/api/tasks/task_001"))["task"]
    route = unwrap(
        client.post(
            "/api/routes/plan",
            json={"task_id": task["id"], "start": task["start"], "target": task["target"], "modes": ["balanced"]},
        )
    )[0]

    simulation = unwrap(client.post("/api/simulations/start", json={"task_id": task["id"], "route": route}))
    assert simulation["events"][0]["type"] == "start"

    current_position = route["points"][len(route["points"]) // 2]
    temporary = unwrap(
        client.post(
            f"/api/simulations/{simulation['simulation_id']}/temporary-risk",
            json={"task_id": task["id"], "current_position": current_position, "time_s": 120},
        )
    )
    assert temporary["affected"] is True

    replanned = unwrap(
        client.post(
            "/api/routes/replan",
            json={
                "task_id": task["id"],
                "current_position": current_position,
                "target": task["target"],
                "temporary_risks": [temporary["risk"]],
                "time_s": 128,
            },
        )
    )
    assert replanned["route"]["id"] == "route_replanned_001"

    report = unwrap(client.get(f"/api/reports/{task['id']}"))
    assert report["recommended_route"]["mode"] == "balanced"
    assert report["vision"]["candidate_count"] >= 1


def test_vision_top_k_and_error_contract():
    images = unwrap(client.get("/api/vision/images?task_id=task_001"))
    tiles = unwrap(client.get("/api/vision/tiles?task_id=task_001"))
    assert len(images) >= 3
    assert len(tiles) >= 5

    result = unwrap(
        client.post(
            "/api/vision/match",
            json={"task_id": "task_001", "image_id": images[0]["id"], "top_k": 2, "algorithm_mode": "precomputed"},
        )
    )
    assert result["candidate_count"] == 2
    assert result["total_candidate_count"] >= result["candidate_count"]
    assert [candidate["rank"] for candidate in result["candidates"]] == [1, 2]

    error = client.get("/api/tasks/missing-task")
    assert error.status_code == 404
    payload = error.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert "task not found" in payload["message"]
