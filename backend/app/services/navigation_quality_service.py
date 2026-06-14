import math

from app.services.geometry import distance_m


def summarize_navigation_quality(session: dict, task: dict) -> dict:
    timeline = session.get("timeline", [])
    route = session.get("route", {})
    origin = task["area"]["coordinates"][0][0]
    visual_frames = [frame for frame in timeline if frame.get("visual_position")]
    confidences = [frame["visual_position"].get("confidence", 0) for frame in visual_frames]
    visual_errors = [frame.get("deviation_m", 0) for frame in visual_frames]
    error_radii = [frame["visual_position"].get("error_radius_m", 0) for frame in visual_frames]
    fused_deviations = [_fused_deviation(frame, origin) for frame in timeline]
    provider_counts = _counts(
        frame["visual_position"].get("localization_mode", "")
        for frame in visual_frames
        if frame.get("visual_position")
    )
    navigation_mode_counts = _counts(frame.get("navigation_mode", "") for frame in timeline)
    location_source_counts = _counts(frame.get("telemetry", {}).get("location_source", "") for frame in timeline)
    fallback_count = sum(
        1
        for frame in visual_frames
        if "_fallback_from_" in frame["visual_position"].get("localization_mode", "")
    )
    final_error = _final_error_m(timeline, route, origin)
    max_step_mps = _max_step_mps(timeline, origin)
    max_heading_delta_deg = _max_heading_delta_deg(timeline)
    quality_grade = _quality_grade(confidences, fused_deviations, final_error, fallback_count)

    return {
        "matcher_mode": session.get("matcher_mode", "synthetic_v04"),
        "frame_count": len(timeline),
        "visual_observation_count": len(visual_frames),
        "provider_counts": provider_counts,
        "navigation_mode_counts": navigation_mode_counts,
        "location_source_counts": location_source_counts,
        "fallback_count": fallback_count,
        "review_frame_count": navigation_mode_counts.get("review", 0),
        "confidence": {
            "average": _average(confidences),
            "min": round(min(confidences), 3) if confidences else 0,
            "max": round(max(confidences), 3) if confidences else 0,
            "low_confidence_count": sum(1 for value in confidences if value < 0.75),
            "navigation_grade_count": sum(1 for value in confidences if value >= 0.5),
            "autonomous_grade_count": sum(1 for value in confidences if value >= 0.75),
        },
        "visual_error": {
            "average_m": _average(visual_errors, 1),
            "max_m": round(max(visual_errors), 1) if visual_errors else 0,
            "average_error_radius_m": _average(error_radii, 1),
            "max_error_radius_m": round(max(error_radii), 1) if error_radii else 0,
        },
        "fused_trajectory": {
            "average_deviation_m": _average(fused_deviations, 1),
            "max_deviation_m": round(max(fused_deviations), 1) if fused_deviations else 0,
            "final_error_m": final_error,
            "max_step_mps": max_step_mps,
            "max_heading_delta_deg": max_heading_delta_deg,
            "smoothness_passed": max_step_mps <= 10.1 and max_heading_delta_deg <= 20,
        },
        "quality_grade": quality_grade,
        "summary": _summary(quality_grade, len(visual_frames), confidences, fused_deviations, final_error, fallback_count),
    }


def _fused_deviation(frame: dict, origin: list[float]) -> float:
    return distance_m(_pose_to_point(frame["reference_position"]), _pose_to_point(frame["fused_position"]), origin)


def _final_error_m(timeline: list[dict], route: dict, origin: list[float]) -> float:
    if not timeline or not route.get("points"):
        return 0.0
    return round(distance_m(_pose_to_point(timeline[-1]["fused_position"]), route["points"][-1], origin), 1)


def _max_step_mps(timeline: list[dict], origin: list[float]) -> float:
    max_step = 0.0
    for previous, current in zip(timeline, timeline[1:]):
        previous_point = _pose_to_point(previous["fused_position"])
        current_point = _pose_to_point(current["fused_position"])
        delta_t = max(1, current["time_s"] - previous["time_s"])
        max_step = max(max_step, distance_m(previous_point, current_point, origin) / delta_t)
    return round(max_step, 1)


def _max_heading_delta_deg(timeline: list[dict]) -> float:
    headings = []
    for previous, current in zip(timeline, timeline[1:]):
        heading = _bearing_degrees(_pose_to_point(previous["fused_position"]), _pose_to_point(current["fused_position"]))
        if heading is not None:
            headings.append(heading)
    deltas = [abs(((current - previous + 540) % 360) - 180) for previous, current in zip(headings, headings[1:])]
    return round(max(deltas, default=0), 1)


def _bearing_degrees(start: list[float], end: list[float]) -> float | None:
    avg_lat = math.radians((start[1] + end[1]) / 2)
    east_m = (end[0] - start[0]) * 111320 * math.cos(avg_lat)
    north_m = (end[1] - start[1]) * 111320
    if abs(east_m) + abs(north_m) < 0.01:
        return None
    return (math.degrees(math.atan2(east_m, north_m)) + 360) % 360


def _quality_grade(
    confidences: list[float],
    fused_deviations: list[float],
    final_error_m: float,
    fallback_count: int,
) -> str:
    average_confidence = _average(confidences)
    average_fused_deviation = _average(fused_deviations, 1)
    max_fused_deviation = max(fused_deviations) if fused_deviations else 0
    if average_confidence >= 0.75 and average_fused_deviation <= 5 and max_fused_deviation <= 12 and final_error_m <= 5 and fallback_count == 0:
        return "navigation_verified"
    if average_confidence >= 0.65 and average_fused_deviation <= 10 and final_error_m <= 10:
        return "demo_verified"
    return "review_required"


def _summary(
    quality_grade: str,
    visual_count: int,
    confidences: list[float],
    fused_deviations: list[float],
    final_error_m: float,
    fallback_count: int,
) -> str:
    grade_text = {
        "navigation_verified": "视觉导航状态更新稳定",
        "demo_verified": "视觉导航演示链路可用",
        "review_required": "视觉导航质量需要复核",
    }[quality_grade]
    average_confidence = round(_average(confidences) * 100)
    average_fused = _average(fused_deviations, 1)
    fallback_text = "未触发真实 matcher 回退" if fallback_count == 0 else f"触发 {fallback_count} 帧回退"
    return (
        f"{grade_text}：共 {visual_count} 帧视觉观测，平均置信度 {average_confidence}%，"
        f"融合轨迹平均偏差 {average_fused}m，终点误差 {final_error_m}m，{fallback_text}。"
    )


def _counts(values) -> dict:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _average(values: list[float], digits: int = 3) -> float:
    if not values:
        return 0
    return round(sum(values) / len(values), digits)


def _pose_to_point(pose: dict) -> list[float]:
    return [pose["lon"], pose["lat"], pose["altitude_m"]]
