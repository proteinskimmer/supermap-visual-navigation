from __future__ import annotations

from math import atan2, degrees

from app.services.geometry import distance_m, lonlat_to_xy
from app.services.vision_matcher_provider import build_semi_real_uav_frame, default_camera_calibration


DISTANCE_INTERVAL_M = 280.0
MIN_FRAME_GAP_S = 18
TURN_THRESHOLD_DEG = 24.0


def build_auto_vision_images(task: dict, route: dict, tiles: list[dict], max_frames: int = 8) -> list[dict]:
    points = route.get("points", [])
    if len(points) < 2:
        return []
    origin = task["area"]["coordinates"][0][0]
    samples = _route_samples(points, origin)
    if not samples:
        return []

    total_distance = samples[-1]["distance_m"]
    duration = max(route.get("estimated_time_s", 1), 1)
    selected = []
    next_distance = DISTANCE_INTERVAL_M

    for sample in samples:
        trigger = ""
        if sample["index"] == 0:
            continue
        if sample["distance_m"] >= next_distance:
            trigger = "distance_interval"
            next_distance += DISTANCE_INTERVAL_M
        elif sample.get("turn_deg", 0) >= TURN_THRESHOLD_DEG:
            trigger = "heading_change"
        elif sample["index"] == len(samples) - 1:
            trigger = "route_arrival"
        if not trigger:
            continue
        time_s = round(sample["distance_m"] / max(total_distance, 1) * duration)
        if selected and time_s - selected[-1]["capture_time_s"] < MIN_FRAME_GAP_S and trigger not in {"heading_change", "route_arrival"}:
            continue
        selected.append(_frame_from_sample(task, sample, time_s, trigger, tiles, origin, len(selected) + 1))
        if len(selected) >= max_frames:
            break

    if selected[-1]["frame_trigger"] != "route_arrival" and len(selected) < max_frames:
        sample = samples[-1]
        arrival = _frame_from_sample(task, sample, duration, "route_arrival", tiles, origin, len(selected) + 1)
        if duration - selected[-1]["capture_time_s"] < MIN_FRAME_GAP_S:
            arrival["id"] = selected[-1]["id"]
            selected[-1] = arrival
        else:
            selected.append(arrival)
    return selected


def _route_samples(points: list[list[float]], origin: list[float]) -> list[dict]:
    samples = []
    distance = 0.0
    for index, point in enumerate(points):
        if index:
            distance += distance_m(points[index - 1], point, origin)
        samples.append(
            {
                "index": index,
                "point": point,
                "distance_m": round(distance, 1),
                "heading_deg": _heading(points, index, origin),
                "turn_deg": _turn_angle(points, index, origin),
            }
        )
    if len(points) <= 3:
        return samples

    # Densify long route segments so distance-based frame selection is not limited by route vertices.
    dense = []
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        start_distance = samples[index]["distance_m"]
        segment_distance = distance_m(start, end, origin)
        steps = max(1, int(segment_distance // DISTANCE_INTERVAL_M) + 1)
        for step in range(steps):
            ratio = step / steps
            point = _lerp_point(start, end, ratio)
            dense.append(
                {
                    "index": len(dense),
                    "point": point,
                    "distance_m": round(start_distance + segment_distance * ratio, 1),
                    "heading_deg": _bearing(start, end, origin),
                    "turn_deg": samples[index].get("turn_deg", 0),
                }
            )
    final_sample = dict(samples[-1])
    final_sample["index"] = len(dense)
    dense.append(final_sample)
    return dense


def _frame_from_sample(
    task: dict,
    sample: dict,
    time_s: int,
    trigger: str,
    tiles: list[dict],
    origin: list[float],
    frame_number: int,
) -> dict:
    point = sample["point"]
    tile = _nearest_tile(point, tiles, origin)
    source_tile_image = tile.get("tile_image") if tile else "/demo/luojia_ortho_preview.jpg"
    frame_id = f"auto_uav_{frame_number:03d}"
    camera = {
        "fov_deg": 72,
        "height_m": point[2] if len(point) > 2 else 120,
        "yaw_deg": sample.get("heading_deg", 0),
        "pitch_deg": -40,
        "roll_deg": 0,
    }
    semi_real = build_semi_real_uav_frame(source_tile_image, frame_id, camera["yaw_deg"], camera["fov_deg"], point)
    calibration = semi_real.get("camera_calibration", default_camera_calibration())
    return {
        "id": frame_id,
        "task_id": task["id"],
        "name": f"自动合成视觉帧 {frame_number:02d}",
        "query_image": semi_real["image_url"],
        "capture_time_s": int(time_s),
        "resolution": [1280, 720],
        "camera": camera,
        "camera_calibration": calibration,
        "distortion_model": calibration.get("distortion_model", "plumb_bob"),
        "distortion_coefficients": calibration.get("distortion_coefficients", {}),
        "scene_tags": ["luojia", "synthetic", "dem", "ortho", "building"],
        "expected_center": [point[0], point[1], point[2] if len(point) > 2 else 120.0],
        "source": "semi_real_uav_frame_simulator",
        "frame_trigger": trigger,
        "route_distance_m": sample["distance_m"],
        "source_tile_id": tile.get("tile_id", "") if tile else "",
        "source_tile_image": source_tile_image,
        "uav_frame_simulation": semi_real,
        "synthetic_view_note": "Frame image is derived from the orthophoto tile selected along the route; DEM/building context is used during synthetic-view localization.",
    }


def _nearest_tile(point: list[float], tiles: list[dict], origin: list[float]) -> dict | None:
    if not tiles:
        return None
    return min(tiles, key=lambda tile: distance_m(point, tile["center"], origin))


def _heading(points: list[list[float]], index: int, origin: list[float]) -> float:
    if index < len(points) - 1:
        return _bearing(points[index], points[index + 1], origin)
    if index > 0:
        return _bearing(points[index - 1], points[index], origin)
    return 0.0


def _turn_angle(points: list[list[float]], index: int, origin: list[float]) -> float:
    if index <= 0 or index >= len(points) - 1:
        return 0.0
    prev_heading = _bearing(points[index - 1], points[index], origin)
    next_heading = _bearing(points[index], points[index + 1], origin)
    delta = abs((next_heading - prev_heading + 180) % 360 - 180)
    return round(delta, 1)


def _bearing(start: list[float], end: list[float], origin: list[float]) -> float:
    sx, sy = lonlat_to_xy(start, origin)
    ex, ey = lonlat_to_xy(end, origin)
    return round((degrees(atan2(ex - sx, ey - sy)) + 360) % 360, 1)


def _lerp_point(start: list[float], end: list[float], ratio: float) -> list[float]:
    return [
        round(start[0] + (end[0] - start[0]) * ratio, 9),
        round(start[1] + (end[1] - start[1]) * ratio, 9),
        round((start[2] if len(start) > 2 else 120.0) + ((end[2] if len(end) > 2 else 120.0) - (start[2] if len(start) > 2 else 120.0)) * ratio, 1),
    ]
