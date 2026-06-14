from app.services.geometry import (
    distance_m,
    point_in_polygon,
    point_to_segment_distance_m,
    polyline_distance_m,
    segment_intersects_polygon,
    segment_to_polygon_distance_m,
)


def analyze_route(task: dict, route: dict, risk_zones: list[dict], obstacles: list[dict]) -> dict:
    origin = [task["area"]["coordinates"][0][0][0], task["area"]["coordinates"][0][0][1]]
    segments = []
    score = 100

    for segment_index in range(len(route["points"]) - 1):
        start = route["points"][segment_index]
        end = route["points"][segment_index + 1]
        for zone in risk_zones:
            if not zone.get("active", True):
                continue
            hit_type = _risk_segment_hit_type(start, end, zone, origin)
            if not hit_type:
                continue
            deduct = zone.get("level", 3) * (10 if hit_type == "inside" else 6)
            score -= deduct
            segments.append(
                {
                    "segment_id": f"risk_zone_{segment_index}_{zone['id']}",
                    "start_index": segment_index,
                    "end_index": segment_index + 1,
                    "risk_type": zone["type"],
                    "risk_level": "high" if zone.get("level", 3) >= 4 else "medium",
                    "reason": f"航线{'穿越' if hit_type == 'inside' else '贴近'}{zone['name']}及安全缓冲区",
                    "deduct_score": deduct,
                }
            )

    for segment_index in range(len(route["points"]) - 1):
        start = route["points"][segment_index]
        end = route["points"][segment_index + 1]
        for obstacle in obstacles:
            gap = point_to_segment_distance_m(obstacle["position"], start, end, origin)
            if gap < obstacle.get("buffer_m", 50):
                deduct = 12
                score -= deduct
                segments.append(
                    {
                        "segment_id": f"obstacle_{segment_index}_{obstacle['id']}",
                        "start_index": segment_index,
                        "end_index": segment_index + 1,
                        "risk_type": "near_obstacle",
                        "risk_level": "medium",
                        "reason": f"航线距离{obstacle['name']}低于安全缓冲距离",
                        "deduct_score": deduct,
                    }
                )

    distance = polyline_distance_m(route["points"], origin)
    if distance > task["params"]["max_distance_m"]:
        score -= 20
        segments.append(
            {
                "segment_id": "max_distance",
                "start_index": 0,
                "end_index": len(route["points"]) - 1,
                "risk_type": "distance_limit",
                "risk_level": "high",
                "reason": "航线距离超过最大航程约束",
                "deduct_score": 20,
            }
        )

    score = max(0, min(100, score))
    return {
        "score": score,
        "risk_level": _risk_level(score),
        "segments": segments,
        "profile": _build_elevation_profile(route["points"], origin),
        "summary": _summary(score, segments, distance),
        "stats": {
            "distance_m": round(distance, 1),
            "risk_count": len(segments),
            "max_deduct_score": max([segment["deduct_score"] for segment in segments], default=0),
        },
    }


def build_simulation_events(route: dict) -> list[dict]:
    points = route["points"]
    middle = points[len(points) // 2]
    return [
        {
            "time_s": 0,
            "type": "start",
            "title": "任务开始",
            "description": "系统沿选定航线启动三维仿真。",
            "position": points[0],
        },
        {
            "time_s": max(30, route["estimated_time_s"] // 3),
            "type": "vision_match",
            "title": "视觉定位观测",
            "description": "无人机视觉图像已匹配到候选地理区域。",
            "position": middle,
        },
        {
            "time_s": route["estimated_time_s"],
            "type": "arrive",
            "title": "到达目标点",
            "description": "仿真任务完成，可生成任务报告。",
            "position": points[-1],
        },
    ]


def temporary_risk_polygon(current_position: list[float]) -> list[list[float]]:
    lon, lat = current_position[0], current_position[1]
    return [
        [lon - 0.006, lat - 0.004],
        [lon + 0.010, lat - 0.004],
        [lon + 0.010, lat + 0.009],
        [lon - 0.006, lat + 0.009],
        [lon - 0.006, lat - 0.004],
    ]


def _risk_segment_hit_type(start: list[float], end: list[float], zone: dict, origin: list[float]) -> str:
    polygon = zone.get("polygon", [])
    if not polygon:
        return ""
    if point_in_polygon(start, polygon) or point_in_polygon(end, polygon):
        return "inside"
    if segment_intersects_polygon(start, end, polygon, origin):
        return "inside"
    buffer_m = float(zone.get("buffer_m", 0) or 0)
    if buffer_m > 0 and segment_to_polygon_distance_m(start, end, polygon, origin) <= buffer_m:
        return "buffer"
    return ""


def _build_elevation_profile(points: list[list[float]], origin: list[float]) -> list[dict]:
    profile = []
    accumulated = 0.0
    for index, point in enumerate(points):
        if index > 0:
            accumulated += distance_m(points[index - 1], point, origin)
        terrain_height = 42 + ((index * 17) % 36)
        profile.append(
            {
                "distance_m": round(accumulated, 1),
                "terrain_height_m": terrain_height,
                "flight_height_m": point[2],
            }
        )
    return profile


def _risk_level(score: int) -> str:
    if score >= 85:
        return "low"
    if score >= 65:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"


def _summary(score: int, segments: list[dict], distance: float) -> str:
    if not segments:
        return f"航线总长约 {round(distance)} 米，未发现高风险航段，推荐用于演示仿真。"
    main_reason = segments[0]["reason"]
    return f"航线总长约 {round(distance)} 米，识别到 {len(segments)} 个风险点，主要风险为：{main_reason}。当前评分 {score} 分。"
