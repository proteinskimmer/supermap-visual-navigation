from math import atan2, cos, pi, sin

from fastapi import HTTPException

from app.services.auto_vision_frame_service import build_auto_vision_images
from app.services.data_store import get_demo_data, get_task
from app.services.geometry import distance_m, lonlat_to_xy, point_in_polygon, xy_to_lonlat
from app.services.planning_service import replan_route
from app.services.synthetic_view_service import localization_to_visual_frame, localize_with_synthetic_views
from app.services.vision_service import list_query_images
from app.services.vision_matcher_provider import is_precomputed_matcher, normalize_matcher_mode


_sessions: dict[str, dict] = {}
NAVIGATION_FRAME_STEP_S = 3


def start_navigation_session(task_id: str, route: dict, mode: str = "autonomous", matcher_mode: str = "synthetic_v04") -> dict:
    try:
        task = get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    data = get_demo_data()
    normalized_matcher = normalize_matcher_mode(matcher_mode)
    session_id = f"nav_{task_id}_{route['id']}_{normalized_matcher}"
    timeline, events = _build_timeline(session_id, task, route, data, mode, normalized_matcher)
    session = {
        "session_id": session_id,
        "task_id": task_id,
        "active_route_id": route["id"],
        "matcher_mode": normalized_matcher,
        "route": route,
        "duration_s": timeline[-1]["time_s"] if timeline else max(route.get("estimated_time_s", 1), 1),
        "state": "ready",
        "timeline": timeline,
        "events": events,
    }
    _sessions[session_id] = session
    return session


def get_navigation_state(session_id: str, time_s: int) -> dict:
    session = _get_session(session_id)
    timeline = session["timeline"]
    if not timeline:
        raise HTTPException(status_code=404, detail=f"navigation timeline not found: {session_id}")
    return min(timeline, key=lambda frame: abs(frame["time_s"] - time_s))


def get_navigation_timeline(session_id: str) -> dict:
    return _get_session(session_id)


def localize_visual_frame(task_id: str, image_id: str, matcher_mode: str = "synthetic_v04") -> dict:
    image = _image_by_id(task_id, image_id)
    localization = _localize_for_navigation(task_id, image, top_k_tiles=1, matcher_mode=matcher_mode)
    if not localization or not localization.get("matches"):
        raise HTTPException(status_code=404, detail=f"vision localization not found: {image_id}")
    return localization_to_visual_frame(localization, image)


def replan_from_navigation_state(session_id: str, time_s: int, temporary_risks: list[dict]) -> dict:
    session = _get_session(session_id)
    state = get_navigation_state(session_id, time_s)
    task = get_task(session["task_id"])
    data = get_demo_data()
    current_position = _pose_to_point(state["fused_position"])
    risks = data["risk_zones"] + temporary_risks
    route = replan_route(task, risks, current_position, task["target"])
    event = {
        "time_s": state["time_s"],
        "type": "replan",
        "title": "基于融合位置重规划",
        "description": "系统以当前 fused_position 为起点，生成接续安全航线。",
        "position": current_position,
    }
    return {"route": route, "event": event}


def _get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"navigation session not found: {session_id}")
    return session


def _build_timeline(session_id: str, task: dict, route: dict, data: dict, mode: str, matcher_mode: str) -> tuple[list[dict], list[dict]]:
    tiles = [tile for tile in data.get("vision_tile_index", []) if tile.get("task_id") == task["id"]]
    images = sorted(build_auto_vision_images(task, route, tiles), key=lambda image: image.get("capture_time_s", 0))
    if not images:
        images = sorted(list_query_images(task["id"]), key=lambda image: image.get("capture_time_s", 0))
    duration = max(route.get("estimated_time_s", 1), 1)
    origin = [task["area"]["coordinates"][0][0][0], task["area"]["coordinates"][0][0][1]]
    route_path = _smooth_route_path(route["points"], origin)
    frame_times = sorted({*range(0, duration + 1, NAVIGATION_FRAME_STEP_S), duration, *[image["capture_time_s"] for image in images]})
    visual_fixes = _build_visual_fixes(task["id"], images, matcher_mode)
    events = _build_base_events(task, route, images, visual_fixes)
    timeline = []
    previous_frame = None
    risk_event_added = False

    for time_s in frame_times:
        frame = _build_state_frame(
            session_id=session_id,
            task=task,
            route=route,
            route_path=route_path,
            time_s=time_s,
            duration=duration,
            origin=origin,
            visual_fixes=visual_fixes,
            all_events=events,
            requested_mode=mode,
            previous_frame=previous_frame,
        )
        risk_event = _risk_event_for_frame(frame, data["risk_zones"])
        if risk_event and not risk_event_added:
            events.append(risk_event)
            risk_event_added = True
            frame["events"].append(risk_event)
            frame["active_event"] = risk_event
        timeline.append(frame)
        previous_frame = frame

    review_events = [event for event in events if event["type"] == "review_required"]
    if review_events:
        review = review_events[0]
        events.append(
            {
                "time_s": review["time_s"] + 4,
                "type": "replan_ready",
                "title": "已进入复核/重规划待命",
                "description": "低置信视觉定位不直接修正主位置，系统保留当前融合位置并等待安全策略接管。",
                "position": review["position"],
            }
        )

    events = sorted(events, key=lambda event: (event["time_s"], event["type"]))
    for frame in timeline:
        frame_events = [event for event in events if event["time_s"] <= frame["time_s"]]
        frame["events"] = [event for event in events if event["time_s"] == frame["time_s"]]
        frame["active_event"] = frame_events[-1] if frame_events else None
    return timeline, events


def _build_visual_fixes(task_id: str, images: list[dict], matcher_mode: str = "synthetic_v04") -> list[dict]:
    fixes = []
    for image in images:
        localization = _localize_for_navigation(task_id, image, top_k_tiles=3, matcher_mode=matcher_mode)
        if not localization or not localization.get("matches") or not localization.get("best_estimated_pose"):
            continue
        match = localization["matches"][0]
        estimated_pose = localization["best_estimated_pose"]
        confidence = localization.get("confidence", 0)
        fixes.append(
            {
                "capture_time_s": image["capture_time_s"],
                "image": image,
                "localization": localization,
                "match": match,
                "mode": _mode_for_confidence(confidence),
                "visual_frame": localization_to_visual_frame(localization, image),
                "route_prior_position": {
                    "lon": localization["route_prior_pose"]["lon"],
                    "lat": localization["route_prior_pose"]["lat"],
                    "altitude_m": localization["route_prior_pose"]["altitude_m"],
                },
                "visual_position": {
                    "lon": estimated_pose["lon"],
                    "lat": estimated_pose["lat"],
                    "altitude_m": estimated_pose["altitude_m"],
                    "confidence": confidence,
                    "tile_id": match.get("tile_id", ""),
                    "match_id": localization.get("localization_id", ""),
                    "image_id": image["id"],
                    "reason": _visual_reason(localization, match),
                    "error_radius_m": localization.get("error_radius_m", 0),
                    "correction_vector_m": localization.get("correction_vector_m", []),
                    "synthetic_view_id": match.get("view_id", ""),
                    "localization_mode": localization.get("provider", ""),
                },
            }
        )
    return fixes


def _localize_for_navigation(task_id: str, image: dict, top_k_tiles: int, matcher_mode: str) -> dict:
    normalized_matcher = normalize_matcher_mode(matcher_mode)
    localization = localize_with_synthetic_views(
        task_id,
        image["id"],
        top_k_tiles=top_k_tiles,
        image_override=image,
        matcher_mode=normalized_matcher,
    )
    if _is_navigation_grade(localization) or is_precomputed_matcher(normalized_matcher):
        return localization

    fallback = localize_with_synthetic_views(
        task_id,
        image["id"],
        top_k_tiles=top_k_tiles,
        image_override=image,
        matcher_mode="precomputed_proxy",
    )
    fallback["provider"] = f"{fallback.get('provider', 'synthetic_view_v04_precomputed_proxy')}_fallback_from_{normalized_matcher}"
    fallback["navigation_effect"] = (
        f"{normalized_matcher} did not produce a navigation-grade observation; "
        "navigation fell back to the v0.4 precomputed proxy"
    )
    fallback["failure_reason"] = localization.get("failure_reason", "")
    fallback.setdefault("pipeline", []).append(f"fallback_from_{normalized_matcher}")
    return fallback


def _is_navigation_grade(localization: dict | None) -> bool:
    return bool(
        localization
        and localization.get("status") == "localized"
        and localization.get("best_estimated_pose")
        and localization.get("matches")
    )


def _visual_reason(localization: dict, match: dict) -> str:
    reason = match.get("reason") or localization.get("failure_reason", "")
    provider = localization.get("provider", "")
    if "_fallback_from_" in provider:
        return f"{reason}；真实 matcher 未达到导航门槛，已回退 v0.4 proxy"
    return reason


def _build_state_frame(
    session_id: str,
    task: dict,
    route: dict,
    route_path: list[list[float]],
    time_s: int,
    duration: int,
    origin: list[float],
    visual_fixes: list[dict],
    all_events: list[dict],
    requested_mode: str,
    previous_frame: dict | None,
) -> dict:
    reference_point = _interpolate_route_point(route_path, time_s / max(duration, 1), origin)
    active_fix = _active_visual_fix(visual_fixes, time_s)
    visual_position = active_fix["visual_position"] if active_fix else None
    visual_frame = active_fix["visual_frame"] if active_fix else None
    navigation_mode = _navigation_mode(active_fix, requested_mode)
    fused_point = _fused_point(reference_point, active_fix, time_s, navigation_mode, previous_frame, origin)
    deviation = distance_m(reference_point, _pose_to_point(visual_position), origin) if visual_position else 0.0
    telemetry = _telemetry(
        time_s=time_s,
        duration=duration,
        fused_point=fused_point,
        reference_point=reference_point,
        next_point=_interpolate_route_point(route_path, min(1, (time_s + NAVIGATION_FRAME_STEP_S) / max(duration, 1)), origin),
        previous_frame=previous_frame,
        navigation_mode=navigation_mode,
        visual_position=visual_position,
        origin=origin,
    )
    exact_events = [event for event in all_events if event["time_s"] == time_s]
    active_events = [event for event in all_events if event["time_s"] <= time_s]
    return {
        "session_id": session_id,
        "time_s": time_s,
        "reference_position": _pose(reference_point),
        "visual_position": visual_position,
        "fused_position": _pose(fused_point),
        "deviation_m": round(deviation, 1),
        "navigation_mode": navigation_mode,
        "telemetry": telemetry,
        "visual_frame": visual_frame,
        "active_frame_id": visual_frame["image_id"] if visual_frame else "",
        "active_route_id": route["id"],
        "active_event": active_events[-1] if active_events else None,
        "events": exact_events,
    }


def _build_base_events(task: dict, route: dict, images: list[dict], visual_fixes: list[dict]) -> list[dict]:
    events = [
        {
            "time_s": 0,
            "type": "navigation_start",
            "title": "导航会话启动",
            "description": "后端已生成权威导航时间线，UAV、遥测、视觉帧和事件流进入统一时钟。",
            "position": route["points"][0],
        }
    ]
    fixes_by_image = {fix["image"]["id"]: fix for fix in visual_fixes}
    for image in images:
        fix = fixes_by_image.get(image["id"])
        if not fix:
            continue
        match = fix["match"]
        confidence = round(match.get("confidence", 0) * 100)
        event_type = "review_required" if fix["mode"] == "review" else "vision_localized"
        if image.get("frame_trigger") == "route_arrival" and fix["mode"] != "review":
            event_type = "landing_correction"
        title = "视觉定位进入复核" if fix["mode"] == "review" else "视觉定位更新"
        events.append(
            {
                "time_s": image["capture_time_s"],
                "type": event_type,
                "title": title,
                "description": (
                    f"{image['id']} 匹配到合成视图 {match.get('view_id')}，置信度 {confidence}%，"
                    f"误差半径 {match.get('error_radius_m')}m，后端按 {fix['mode']} 模式更新导航状态。"
                ),
                "position": _pose_to_point(fix["visual_position"]),
            }
        )
    events.append(
        {
            "time_s": max(route.get("estimated_time_s", 1), 1),
            "type": "arrive",
            "title": "到达目标点",
            "description": "导航时间线已推进至任务目标附近，可生成任务报告。",
            "position": route["points"][-1],
        }
    )
    return events


def _risk_event_for_frame(frame: dict, risk_zones: list[dict]) -> dict | None:
    point = _pose_to_point(frame["fused_position"])
    for zone in risk_zones:
        if zone.get("active", True) and point_in_polygon(point, zone["polygon"]):
            return {
                "time_s": frame["time_s"],
                "type": "risk_alert",
                "title": "融合位置进入风险区",
                "description": f"当前 fused_position 落入或贴近{zone['name']}，后端事件流标记为安全策略待接管。",
                "position": point,
            }
    visual = frame.get("visual_position")
    if visual:
        visual_point = _pose_to_point(visual)
        for zone in risk_zones:
            if zone.get("active", True) and point_in_polygon(visual_point, zone["polygon"]):
                return {
                    "time_s": frame["time_s"],
                    "type": "risk_alert",
                    "title": "视觉定位提示风险接近",
                    "description": f"视觉定位结果位于{zone['name']}附近，系统保留重规划触发依据。",
                    "position": visual_point,
                }
    return None


def _visual_frame(image: dict, result: dict, candidate: dict) -> dict:
    return {
        "image_id": image["id"],
        "name": image["name"],
        "query_image": image["query_image"],
        "capture_time_s": image["capture_time_s"],
        "confidence": candidate.get("confidence", 0),
        "matched_points": candidate.get("matched_points", 0),
        "inlier_ratio": candidate.get("inlier_ratio", 0),
        "tile_id": candidate.get("tile_id", ""),
        "status": result.get("status", candidate.get("status", "")),
        "reason": candidate.get("reason", ""),
    }


def _active_visual_fix(fixes: list[dict], time_s: int) -> dict | None:
    active = [fix for fix in fixes if fix["capture_time_s"] <= time_s]
    return active[-1] if active else None


def _navigation_mode(active_fix: dict | None, requested_mode: str) -> str:
    if not active_fix:
        return "assisted" if requested_mode == "assisted" else "autonomous"
    if requested_mode == "assisted" and active_fix["mode"] != "review":
        return "assisted"
    return active_fix["mode"]


def _mode_for_confidence(confidence: float) -> str:
    if confidence >= 0.75:
        return "autonomous"
    if confidence >= 0.5:
        return "assisted"
    return "review"


def _fused_point(
    reference_point: list[float],
    active_fix: dict | None,
    time_s: int,
    navigation_mode: str,
    previous_frame: dict | None,
    origin: list[float],
) -> list[float]:
    if not active_fix:
        target_point = reference_point
        confidence = 0.0
        observation_weight = 0.0
    else:
        visual_point = _pose_to_point(active_fix["visual_position"])
        elapsed = max(0, time_s - active_fix["capture_time_s"])
        confidence = active_fix["visual_position"]["confidence"]
        if navigation_mode == "autonomous":
            observation_weight = confidence * _freshness_weight(elapsed)
            target_point = _corrected_reference_point(
                reference_point,
                _pose_to_point(active_fix.get("route_prior_position")),
                visual_point,
                observation_weight,
                10.0,
                origin,
            )
        elif navigation_mode == "assisted":
            observation_weight = min(0.35, confidence * 0.45) * _freshness_weight(elapsed)
            target_point = _corrected_reference_point(
                reference_point,
                _pose_to_point(active_fix.get("route_prior_position")),
                visual_point,
                observation_weight,
                6.0,
                origin,
            )
        else:
            observation_weight = 0.0
            target_point = reference_point
    if not previous_frame:
        return target_point

    previous_point = _pose_to_point(previous_frame["fused_position"])
    delta_t = max(1, time_s - previous_frame["time_s"])
    if observation_weight <= 0.001 or navigation_mode == "review":
        alpha = 1.0
        max_speed_mps = 10.0
    elif navigation_mode == "autonomous":
        alpha = 1.0
        max_speed_mps = 10.0
    elif navigation_mode == "assisted":
        alpha = 1.0
        max_speed_mps = 10.0
    else:
        alpha = 1.0
        max_speed_mps = 18.0

    smoothed = [
        round(_lerp(previous_point[0], target_point[0], alpha), 6),
        round(_lerp(previous_point[1], target_point[1], alpha), 6),
        round(_lerp(previous_point[2], target_point[2], alpha), 1),
    ]
    return _limit_step(previous_point, smoothed, max_speed_mps * delta_t, origin)


def _freshness_weight(elapsed_s: int) -> float:
    if elapsed_s <= 0:
        return 0.0
    ramp_in = min(1.0, elapsed_s / 6.0)
    fade_out = max(0.0, 1.0 - elapsed_s / 30.0)
    return _smoothstep(ramp_in) * _smoothstep(fade_out)


def _smoothstep(value: float) -> float:
    clamped = max(0.0, min(1.0, value))
    return clamped * clamped * (3 - 2 * clamped)


def _corrected_reference_point(
    reference_point: list[float],
    route_prior_point: list[float],
    visual_point: list[float],
    weight: float,
    max_horizontal_m: float,
    origin: list[float],
) -> list[float]:
    if weight <= 0:
        return reference_point
    prior_x, prior_y = lonlat_to_xy(route_prior_point, origin)
    visual_x, visual_y = lonlat_to_xy(visual_point, origin)
    dx = visual_x - prior_x
    dy = visual_y - prior_y
    horizontal = (dx**2 + dy**2) ** 0.5
    if horizontal > max_horizontal_m and horizontal > 0:
        ratio = max_horizontal_m / horizontal
        dx *= ratio
        dy *= ratio

    ref_x, ref_y = lonlat_to_xy(reference_point, origin)
    lon, lat = xy_to_lonlat(ref_x + dx * weight, ref_y + dy * weight, origin)
    altitude_delta = max(-4.0, min(4.0, visual_point[2] - route_prior_point[2])) * min(weight, 0.4)
    return [round(lon, 6), round(lat, 6), round(reference_point[2] + altitude_delta, 1)]


def _limit_step(previous_point: list[float], target_point: list[float], max_step_m: float, origin: list[float]) -> list[float]:
    step = distance_m(previous_point, target_point, origin)
    if step <= max_step_m or step == 0:
        return target_point
    ratio = max_step_m / step
    return [
        round(_lerp(previous_point[0], target_point[0], ratio), 6),
        round(_lerp(previous_point[1], target_point[1], ratio), 6),
        round(_lerp(previous_point[2], target_point[2], ratio), 1),
    ]


def _telemetry(
    time_s: int,
    duration: int,
    fused_point: list[float],
    reference_point: list[float],
    next_point: list[float],
    previous_frame: dict | None,
    navigation_mode: str,
    visual_position: dict | None,
    origin: list[float],
) -> dict:
    previous_point = _pose_to_point(previous_frame["fused_position"]) if previous_frame else fused_point
    delta_t = max(1, time_s - previous_frame["time_s"]) if previous_frame else 1
    speed = min(16.0, distance_m(previous_point, fused_point, origin) / delta_t) if previous_frame else 0.0
    heading = _bearing_degrees(fused_point, next_point or reference_point)
    progress = min(1, time_s / max(duration, 1))
    signal = "review" if navigation_mode == "review" else "degraded" if navigation_mode == "assisted" else "nominal"
    source = {
        "autonomous": "visual_fusion" if visual_position else "reference_route",
        "assisted": "visual_assisted" if visual_position else "reference_route",
        "review": "manual_review",
    }[navigation_mode]
    return {
        "uav_id": "UAV-011",
        "speed_mps": round(speed, 1),
        "heading_deg": heading,
        "pitch_deg": -7.0 if speed > 0 else -2.0,
        "roll_deg": round(sin(time_s / 11) * (6 if speed > 0 else 1), 1),
        "yaw_deg": heading,
        "battery_pct": max(18, round(96 - progress * 44)),
        "signal": signal,
        "flight_time": _format_clock(time_s),
        "location_source": source,
    }


def _smooth_route_path(points: list[list[float]], origin: list[float]) -> list[list[float]]:
    if len(points) <= 2:
        return [_normalize_point(point) for point in points]
    path = [_normalize_point(point) for point in points]
    for _ in range(2):
        refined = [path[0]]
        for start, end in zip(path, path[1:]):
            refined.append(_lerp_point_meters(start, end, 0.28, origin))
            refined.append(_lerp_point_meters(start, end, 0.72, origin))
        refined.append(path[-1])
        path = refined
    path[0] = _normalize_point(points[0])
    path[-1] = _normalize_point(points[-1])
    return _deduplicate_path(path)


def _lerp_point_meters(start: list[float], end: list[float], ratio: float, origin: list[float]) -> list[float]:
    start_x, start_y = lonlat_to_xy(start, origin)
    end_x, end_y = lonlat_to_xy(end, origin)
    lon, lat = xy_to_lonlat(_lerp(start_x, end_x, ratio), _lerp(start_y, end_y, ratio), origin)
    return [round(lon, 6), round(lat, 6), round(_lerp(start[2], end[2], ratio), 1)]


def _deduplicate_path(points: list[list[float]]) -> list[list[float]]:
    result = []
    for point in points:
        if result and point[0] == result[-1][0] and point[1] == result[-1][1] and point[2] == result[-1][2]:
            continue
        result.append(point)
    return result


def _interpolate_route_point(points: list[list[float]], progress_ratio: float, origin: list[float]) -> list[float]:
    if not points:
        return [0, 0, 120]
    if len(points) == 1:
        return _normalize_point(points[0])
    clamped = max(0.0, min(1.0, progress_ratio))
    distances = [0.0]
    for start, end in zip(points, points[1:]):
        distances.append(distances[-1] + distance_m(start, end, origin))
    total = max(distances[-1], 1.0)
    target_distance = clamped * total
    start_index = 0
    for index in range(len(distances) - 1):
        if distances[index] <= target_distance <= distances[index + 1]:
            start_index = index
            break
    segment_distance = max(distances[start_index + 1] - distances[start_index], 1.0)
    local_ratio = (target_distance - distances[start_index]) / segment_distance
    start = _normalize_point(points[start_index])
    end = _normalize_point(points[start_index + 1])
    return [
        round(_lerp(start[0], end[0], local_ratio), 6),
        round(_lerp(start[1], end[1], local_ratio), 6),
        round(_lerp(start[2], end[2], local_ratio), 1),
    ]


def _image_by_id(task_id: str, image_id: str) -> dict:
    for image in list_query_images(task_id):
        if image["id"] == image_id:
            return image
    for image in get_demo_data().get("vision_images", []):
        if image.get("task_id") == task_id and image.get("id") == image_id:
            return image
    raise HTTPException(status_code=404, detail=f"vision image not found: {image_id}")


def _pose(point: list[float]) -> dict:
    normalized = _normalize_point(point)
    return {"lon": normalized[0], "lat": normalized[1], "altitude_m": normalized[2]}


def _pose_to_point(pose: dict | None) -> list[float]:
    if not pose:
        return [0, 0, 120]
    return [pose["lon"], pose["lat"], pose["altitude_m"]]


def _normalize_point(point: list[float]) -> list[float]:
    return [point[0], point[1], point[2] if len(point) > 2 else 120.0]


def _lerp(start: float, end: float, ratio: float) -> float:
    return start + (end - start) * ratio


def _bearing_degrees(start: list[float], end: list[float]) -> int:
    lon1 = start[0] * pi / 180
    lon2 = end[0] * pi / 180
    lat1 = start[1] * pi / 180
    lat2 = end[1] * pi / 180
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    return round((atan2(y, x) * 180 / pi + 360) % 360)


def _format_clock(seconds: int) -> str:
    minutes = seconds // 60
    remain = seconds % 60
    return f"{minutes:02d}:{remain:02d}"
