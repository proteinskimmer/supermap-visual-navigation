import math
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import data_store
from app.services.geometry import distance_m


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
    for route in routes:
        route_risk = unwrap(client.post("/api/risks/analyze", json={"task_id": task["id"], "route": route}))
        unsafe_types = {segment["risk_type"] for segment in route_risk["segments"]}
        assert "fire" not in unsafe_types
        assert "landslide" not in unsafe_types

    direct_route = {
        **routes[0],
        "points": [[114.3605, 30.5375, 128.0], [114.3685, 30.5402, 130.0]],
    }
    direct_risk = unwrap(client.post("/api/risks/analyze", json={"task_id": task["id"], "route": direct_route}))
    assert {"fire", "landslide"}.issubset({segment["risk_type"] for segment in direct_risk["segments"]})


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
    assert report["vision_summary"]["image_count"] >= 4
    assert report["vision_summary"]["needs_review_count"] == 0
    assert report["navigation_quality"]["matcher_mode"] == "opencv_auto"
    assert report["navigation_quality"]["visual_observation_count"] >= 6
    assert sum(report["navigation_quality"]["provider_counts"].values()) >= 1
    assert report["navigation_quality"]["confidence"]["average"] >= 0.65
    assert report["navigation_quality"]["fused_trajectory"]["smoothness_passed"] is True
    assert report["navigation_quality"]["fused_trajectory"]["average_deviation_m"] <= 10
    assert report["navigation_quality"]["fused_trajectory"]["max_step_mps"] <= 10.1
    assert report["navigation_quality"]["fused_trajectory"]["max_heading_delta_deg"] <= 20
    assert any(event["type"] == "vision_match" for event in report["events"])


def test_vision_top_k_and_error_contract():
    images = unwrap(client.get("/api/vision/images?task_id=task_001"))
    tiles = unwrap(client.get("/api/vision/tiles?task_id=task_001"))
    assert len(images) >= 3
    assert len(tiles) >= 5
    assert all(image["id"].startswith("auto_uav_") for image in images)
    assert all(image["query_image"] for image in images)
    assert any(image["frame_trigger"] in {"distance_interval", "heading_change", "route_arrival"} for image in images)

    result = unwrap(
        client.post(
            "/api/vision/match",
            json={"task_id": "task_001", "image_id": images[0]["id"], "top_k": 2, "algorithm_mode": "precomputed"},
        )
    )
    assert result["candidate_count"] == 2
    assert result["total_candidate_count"] >= result["candidate_count"]
    assert [candidate["rank"] for candidate in result["candidates"]] == [1, 2]

    landing_correction = unwrap(
        client.post(
            "/api/vision/match",
            json={"task_id": "task_001", "image_id": images[-1]["id"], "top_k": 1, "algorithm_mode": "precomputed"},
        )
    )
    assert images[-1]["frame_trigger"] == "route_arrival"
    assert landing_correction["candidates"][0]["confidence"] >= 0.75
    assert landing_correction["candidates"][0]["status"] == "best"

    error = client.get("/api/tasks/missing-task")
    assert error.status_code == 404
    payload = error.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert "task not found" in payload["message"]


def test_synthetic_view_localization_contract():
    image = unwrap(client.get("/api/vision/images?task_id=task_001"))[0]
    views = unwrap(
        client.post(
            "/api/vision/synthetic-views",
            json={"task_id": "task_001", "image_id": image["id"], "top_k_tiles": 3, "matcher_mode": "precomputed_proxy"},
        )
    )
    assert views["candidate_count"] == 3
    assert views["synthetic_views"][0]["view_id"].startswith(f"syn_{image['id']}")
    assert views["synthetic_views"][0]["render_source"]["mode"].startswith("v0.4")
    assert views["synthetic_views"][0]["terrain_height_m"] >= 0

    localization = unwrap(
        client.post(
            "/api/vision/localize",
            json={"task_id": "task_001", "image_id": image["id"], "top_k_tiles": 3, "matcher_mode": "precomputed_proxy"},
        )
    )
    assert localization["provider"] == "synthetic_view_v04_precomputed_proxy"
    assert localization["status"] == "localized"
    assert localization["best_estimated_pose"]
    assert localization["confidence"] >= 0.75
    assert localization["error_radius_m"] > 0
    assert localization["correction_vector_m"]
    assert localization["matches"][0]["view_id"] == views["synthetic_views"][0]["view_id"]


def test_v05_matcher_provider_status_and_orb_contract():
    image = unwrap(client.get("/api/vision/images?task_id=task_001"))[0]
    lighting = image["uav_frame_simulation"]["lighting_model"]
    assert lighting["longitude_deg"] == image["expected_center"][0]
    assert lighting["latitude_deg"] == image["expected_center"][1]
    matchers = unwrap(client.get("/api/vision/matchers"))
    assert matchers["precomputed_proxy"]["status"] == "available"
    assert "opencv_orb" in matchers
    assert "opencv_sift" in matchers
    assert "opencv_akaze" in matchers
    assert "opencv_brisk" in matchers
    assert "opencv_auto" in matchers

    localization = unwrap(
        client.post(
            "/api/vision/localize",
            json={
                "task_id": "task_001",
                "image_id": image["id"],
                "top_k_tiles": 2,
                "matcher_mode": "opencv_orb",
            },
        )
    )
    assert localization["synthetic_views"]
    if matchers["opencv_orb"]["status"] == "available":
        assert localization["provider"] == "opencv_orb"
        assert localization["status"] in {"localized", "needs_review", "failed"}
        assert localization["image_simulation"]["camera_calibration"]["distortion_coefficients"]["k1"] != 0
        assert localization["image_simulation"]["lighting_model"]["longitude_deg"] == image["expected_center"][0]
        assert localization["matches"]
        assert localization["synthetic_views"][0]["render_source"]["mode"].startswith("v0.5a")
        assert localization["matched_points"] >= 1
        evidence = Path("demo_data/generated/v05_match_evidence")
        assert evidence.exists()
        assert any(evidence.glob(f"{image['id']}_*_opencv_orb_result.json"))
    else:
        assert localization["provider"] == "opencv_orb_unavailable"
        assert localization["status"] == "failed"
        assert localization["confidence"] == 0
        assert localization["matched_points"] == 0
        assert localization["matches"] == []
        assert "OpenCV" in localization["failure_reason"] or "reserved for v0.5" in localization["failure_reason"]

    auto_localization = unwrap(
        client.post(
            "/api/vision/localize",
            json={
                "task_id": "task_001",
                "image_id": image["id"],
                "top_k_tiles": 2,
                "matcher_mode": "opencv_auto",
            },
        )
    )
    assert auto_localization["provider"] == "opencv_auto"
    assert auto_localization["selected_provider"] in {"opencv_orb", "opencv_sift", "opencv_akaze", "opencv_brisk", ""}
    assert auto_localization["provider_results"]
    if auto_localization["matches"]:
        best = auto_localization["matches"][0]
        assert best["provider"] in {"opencv_orb", "opencv_sift", "opencv_akaze", "opencv_brisk"}
        assert "reprojection_error_px" in best
        assert "score_components" in best


def test_risk_zone_edit_save_and_validation_contract(tmp_path, monkeypatch):
    temp_demo_data = tmp_path / "task_demo.json"
    temp_demo_data.write_text(data_store.DEMO_DATA_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(data_store, "DEMO_DATA_PATH", temp_demo_data)
    data_store.load_demo_data.cache_clear()

    original = unwrap(client.get("/api/tasks/task_001/risk-zones"))
    edited = [
        *original,
        {
            "id": "risk_test_editor_001",
            "name": "测试编辑风险区",
            "type": "custom",
            "level": 3,
            "buffer_m": 75,
            "active": True,
            "polygon": [
                [116.156, 39.156],
                [116.162, 39.156],
                [116.162, 39.162],
                [116.156, 39.162],
                [116.156, 39.156],
            ],
        },
    ]

    try:
        saved = unwrap(client.put("/api/tasks/task_001/risk-zones", json={"risk_zones": edited}))
        assert saved["count"] == len(edited)
        assert saved["risk_zones"][-1]["id"] == "risk_test_editor_001"

        detail = unwrap(client.get("/api/tasks/task_001"))
        assert any(zone["id"] == "risk_test_editor_001" for zone in detail["risk_zones"])

        duplicate = client.put("/api/tasks/task_001/risk-zones", json={"risk_zones": [edited[-1], edited[-1]]})
        assert duplicate.status_code == 422
        assert duplicate.json()["success"] is False

        open_polygon = {**edited[-1], "id": "risk_test_open_polygon", "polygon": edited[-1]["polygon"][:-1]}
        invalid = client.put("/api/tasks/task_001/risk-zones", json={"risk_zones": [open_polygon]})
        assert invalid.status_code == 422
        assert invalid.json()["success"] is False
    finally:
        data_store.load_demo_data.cache_clear()


def test_visual_navigation_timeline_contract():
    task = unwrap(client.get("/api/tasks/task_001"))["task"]
    route = unwrap(
        client.post(
            "/api/routes/plan",
            json={"task_id": task["id"], "start": task["start"], "target": task["target"], "modes": ["balanced"]},
        )
    )[0]

    session = unwrap(client.post("/api/navigation/start", json={"task_id": task["id"], "route": route, "mode": "autonomous"}))
    assert session["session_id"]
    assert session["matcher_mode"] == "opencv_auto"
    assert session["active_route_id"] == route["id"]
    assert session["timeline"]
    assert session["events"][0]["type"] == "navigation_start"

    first_frame = session["timeline"][0]
    assert first_frame["fused_position"] == first_frame["reference_position"]
    assert first_frame["telemetry"]["location_source"] == "reference_route"

    high_confidence = unwrap(client.get(f"/api/navigation/state?session_id={session['session_id']}&time_s=92"))
    assert high_confidence["visual_position"]["confidence"] >= 0.75
    assert high_confidence["visual_position"]["synthetic_view_id"]
    assert high_confidence["visual_position"]["error_radius_m"] > 0
    assert high_confidence["visual_frame"]["synthetic_image"]
    assert high_confidence["navigation_mode"] == "autonomous"
    assert high_confidence["telemetry"]["location_source"] == "visual_fusion"
    assert high_confidence["deviation_m"] > 0

    event_types = {event["type"] for event in session["events"]}
    assert "vision_localized" in event_types
    assert "landing_correction" in event_types

    origin = task["area"]["coordinates"][0][0]
    final_frame = session["timeline"][-1]
    final_point = [
        final_frame["fused_position"]["lon"],
        final_frame["fused_position"]["lat"],
        final_frame["fused_position"]["altitude_m"],
    ]
    assert final_frame["time_s"] == route["estimated_time_s"]
    assert final_frame["active_frame_id"].startswith("auto_uav_")
    assert final_frame["navigation_mode"] == "autonomous"
    assert final_frame["visual_position"]["confidence"] >= 0.75
    assert final_frame["active_event"]["type"] == "landing_correction"
    assert distance_m(final_point, route["points"][-1], origin) <= 1.0

    max_step_m = 0
    headings = []
    for previous, current in zip(session["timeline"], session["timeline"][1:]):
        previous_point = [
            previous["fused_position"]["lon"],
            previous["fused_position"]["lat"],
            previous["fused_position"]["altitude_m"],
        ]
        current_point = [
            current["fused_position"]["lon"],
            current["fused_position"]["lat"],
            current["fused_position"]["altitude_m"],
        ]
        delta_t = max(1, current["time_s"] - previous["time_s"])
        max_step_m = max(max_step_m, distance_m(previous_point, current_point, origin) / delta_t)
        heading = _bearing_degrees(previous_point, current_point)
        if heading is not None:
            headings.append(heading)
    assert max_step_m <= 10.1
    max_heading_delta = max(
        [_heading_delta(previous, current) for previous, current in zip(headings, headings[1:])],
        default=0,
    )
    assert max_heading_delta <= 20


def test_visual_navigation_timeline_can_be_orb_driven():
    task = unwrap(client.get("/api/tasks/task_001"))["task"]
    route = unwrap(
        client.post(
            "/api/routes/plan",
            json={"task_id": task["id"], "start": task["start"], "target": task["target"], "modes": ["balanced"]},
        )
    )[0]

    session = unwrap(
        client.post(
            "/api/navigation/start",
            json={
                "task_id": task["id"],
                "route": route,
                "mode": "autonomous",
                "matcher_mode": "opencv_orb",
            },
        )
    )
    assert session["matcher_mode"] == "opencv_orb"
    providers = {
        frame["visual_position"]["localization_mode"]
        for frame in session["timeline"]
        if frame.get("visual_position")
    }
    assert "opencv_orb" in providers

    visual_frames = [frame for frame in session["timeline"] if frame.get("visual_position")]
    assert visual_frames
    assert any(frame["navigation_mode"] == "autonomous" for frame in visual_frames)
    assert any(frame["visual_frame"]["matched_points"] >= 100 for frame in visual_frames)
    assert max(frame["visual_position"]["confidence"] for frame in visual_frames) >= 0.8


def test_navigation_localize_and_replan_contract():
    task = unwrap(client.get("/api/tasks/task_001"))["task"]
    route = unwrap(
        client.post(
            "/api/routes/plan",
            json={"task_id": task["id"], "start": task["start"], "target": task["target"], "modes": ["balanced"]},
        )
    )[0]
    session = unwrap(client.post("/api/navigation/start", json={"task_id": task["id"], "route": route}))

    image = unwrap(client.get("/api/vision/images?task_id=task_001"))[0]
    visual_frame = unwrap(client.post("/api/navigation/localize", json={"task_id": task["id"], "image_id": image["id"]}))
    assert visual_frame["image_id"] == image["id"]
    assert visual_frame["confidence"] >= 0.75
    assert visual_frame["tile_id"]

    replanned = unwrap(
        client.post(
            "/api/navigation/replan",
            json={"session_id": session["session_id"], "time_s": 92, "temporary_risks": []},
        )
    )
    assert replanned["route"]["id"] == "route_replanned_001"
    assert replanned["event"]["type"] == "replan"


def _bearing_degrees(start: list[float], end: list[float]) -> float | None:
    avg_lat = math.radians((start[1] + end[1]) / 2)
    east_m = (end[0] - start[0]) * 111320 * math.cos(avg_lat)
    north_m = (end[1] - start[1]) * 111320
    if abs(east_m) + abs(north_m) < 0.01:
        return None
    return (math.degrees(math.atan2(east_m, north_m)) + 360) % 360


def _heading_delta(previous: float, current: float) -> float:
    return abs(((current - previous + 540) % 360) - 180)
