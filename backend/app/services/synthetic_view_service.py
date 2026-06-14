from __future__ import annotations

import json
from functools import lru_cache
from math import atan2, cos, pi, sin
from pathlib import Path

from fastapi import HTTPException

from app.services.data_store import get_demo_data, get_task
from app.services.geometry import lonlat_to_xy, point_in_polygon, xy_to_lonlat
from app.services.vision_matcher_provider import (
    build_v05a_synthetic_view,
    is_precomputed_matcher,
    is_supported_matcher,
    localize_with_opencv_features,
    localize_with_opencv_orb,
    normalize_matcher_mode,
    unavailable_localization,
)
from app.services.vision_service import get_match_result, list_query_images, list_tile_index


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TERRAIN_PREVIEW = PROJECT_ROOT / "frontend/public/demo/luojia_terrain_preview.json"
BUILDINGS_PREVIEW = PROJECT_ROOT / "frontend/public/demo/luojia_buildings_preview.json"
FALLBACK_ORTHO_IMAGE = "/demo/luojia_ortho_preview.jpg"

PIPELINE = [
    "route_prior_pose",
    "candidate_tile_retrieval",
    "dem_ortho_building_synthetic_view",
    "image_to_synthetic_view_match",
    "pose_back_projection",
    "navigation_observation",
]

DEFAULT_INITIAL_OFFSETS_M = {
    "demo_uav_001": [58.0, -34.0, 0.0],
    "demo_uav_002": [76.0, 41.0, 0.0],
    "demo_uav_003": [-46.0, 32.0, 0.0],
    "demo_uav_004": [112.0, -83.0, 0.0],
}


def build_synthetic_view_response(
    task_id: str,
    image_id: str,
    initial_pose: dict | None = None,
    route_prior_pose: dict | None = None,
    top_k_tiles: int = 3,
    image_override: dict | None = None,
    render_mode: str = "synthetic_v04",
    lighting_options: dict | None = None,
) -> dict:
    task = _task_or_404(task_id)
    image = image_override or _image_or_404(task_id, image_id)
    origin = _origin(task)
    route_prior = _pose_with_defaults(route_prior_pose) if route_prior_pose else _route_prior_pose(image)
    initial = _pose_with_defaults(initial_pose) if initial_pose else _initial_pose(image, route_prior, origin)
    tiles = list_tile_index(task_id)
    selected_tiles = _candidate_tiles(task_id, image_id, tiles, route_prior, top_k_tiles, origin)
    query_image = image["query_image"]
    image_simulation = image.get("uav_frame_simulation", {})
    if render_mode == "v05a" and image.get("source_tile_image"):
        from app.services.vision_matcher_provider import build_semi_real_uav_frame

        image_simulation = build_semi_real_uav_frame(
            image["source_tile_image"],
            image["id"],
            image.get("camera", {}).get("yaw_deg", route_prior["yaw_deg"]),
            image.get("camera", {}).get("fov_deg", 72),
            image.get("expected_center") or [route_prior["lon"], route_prior["lat"], route_prior["altitude_m"]],
            lighting_options,
        )
        query_image = image_simulation["image_url"]
    views = [
        _synthetic_view(task_id, image, tile, route_prior, initial, rank, origin, render_mode, lighting_options)
        for rank, tile in enumerate(selected_tiles, start=1)
    ]
    return {
        "task_id": task_id,
        "image_id": image_id,
        "query_image": query_image,
        "image_simulation": image_simulation,
        "frame_trigger": image.get("frame_trigger", ""),
        "initial_pose": initial,
        "route_prior_pose": route_prior,
        "candidate_count": len(views),
        "synthetic_views": views,
        "pipeline": PIPELINE,
    }


def localize_with_synthetic_views(
    task_id: str,
    image_id: str,
    initial_pose: dict | None = None,
    route_prior_pose: dict | None = None,
    top_k_tiles: int = 3,
    image_override: dict | None = None,
    matcher_mode: str = "opencv_auto",
    lighting_options: dict | None = None,
) -> dict:
    task = _task_or_404(task_id)
    origin = _origin(task)
    normalized_matcher = normalize_matcher_mode(matcher_mode)
    if not is_supported_matcher(normalized_matcher):
        raise HTTPException(status_code=400, detail=f"unsupported matcher mode: {matcher_mode}")
    render_mode = "v05a" if not is_precomputed_matcher(normalized_matcher) else "synthetic_v04"
    response = build_synthetic_view_response(task_id, image_id, initial_pose, route_prior_pose, top_k_tiles, image_override, render_mode, lighting_options)
    if not is_precomputed_matcher(normalized_matcher):
        if normalized_matcher == "opencv_orb":
            return localize_with_opencv_orb(task_id, image_id, response, origin)
        if normalized_matcher.startswith("opencv_"):
            return localize_with_opencv_features(task_id, image_id, response, origin, normalized_matcher)
        return unavailable_localization(task_id, image_id, response, normalized_matcher)

    match_result = _match_result_from_synthetic_views(response) if image_override else get_match_result(task_id, image_id, top_k_tiles)
    view_by_tile = {view["tile_id"]: view for view in response["synthetic_views"]}
    matches = []

    for rank, candidate in enumerate((match_result or {}).get("candidates", []), start=1):
        view = view_by_tile.get(candidate.get("tile_id"))
        if not view:
            continue
        estimated_pose = _estimated_pose_from_candidate(candidate, view)
        correction = _correction_vector_m(response["initial_pose"], estimated_pose, origin)
        confidence = candidate.get("confidence", 0)
        status = _status_for_confidence(confidence, candidate.get("status", ""))
        failure_reason = "" if status in {"best", "candidate"} else _failure_reason(candidate, confidence)
        matches.append(
            {
                "view_id": view["view_id"],
                "tile_id": candidate.get("tile_id", view["tile_id"]),
                "confidence": confidence,
                "matched_points": candidate.get("matched_points", 0),
                "inlier_ratio": candidate.get("inlier_ratio", 0),
                "offset_m": candidate.get("offset_m", [0.0, 0.0]),
                "correction_vector_m": correction,
                "error_radius_m": _error_radius_m(confidence, candidate.get("inlier_ratio", 0)),
                "estimated_pose": estimated_pose,
                "status": status,
                "failure_reason": failure_reason,
                "reason": candidate.get("reason", ""),
                "rank": rank,
            }
        )

    matches.sort(key=lambda item: item["confidence"], reverse=True)
    for rank, item in enumerate(matches, start=1):
        item["rank"] = rank

    best = matches[0] if matches else None
    status = "localized" if best and best["confidence"] >= 0.5 else "needs_review" if best else "failed"
    return {
        "localization_id": f"loc_{image_id}_synthetic_v04",
        "task_id": task_id,
        "image_id": image_id,
        "query_image": response["query_image"],
        "provider": "synthetic_view_v04_precomputed_proxy",
        "status": status,
        "image_simulation": response.get("image_simulation", {}),
        "initial_pose": response["initial_pose"],
        "route_prior_pose": response["route_prior_pose"],
        "best_estimated_pose": best["estimated_pose"] if best else None,
        "confidence": best["confidence"] if best else 0,
        "error_radius_m": best["error_radius_m"] if best else 999,
        "matched_points": best["matched_points"] if best else 0,
        "inlier_ratio": best["inlier_ratio"] if best else 0,
        "correction_vector_m": best["correction_vector_m"] if best else [0.0, 0.0, 0.0],
        "synthetic_views": response["synthetic_views"],
        "matches": matches,
        "navigation_effect": _navigation_effect(status, best),
        "failure_reason": "" if status == "localized" else _localization_failure_reason(best),
        "pipeline": PIPELINE,
    }


def get_localization(task_id: str, image_id: str) -> dict:
    return localize_with_synthetic_views(task_id, image_id)


def localization_to_visual_frame(localization: dict, image: dict) -> dict:
    best = localization["matches"][0] if localization["matches"] else None
    best_view = _view_for_match(localization, best) if best else None
    return {
        "image_id": image["id"],
        "name": image["name"],
        "query_image": image["query_image"],
        "capture_time_s": image["capture_time_s"],
        "confidence": localization["confidence"],
        "matched_points": localization["matched_points"],
        "inlier_ratio": localization["inlier_ratio"],
        "tile_id": best["tile_id"] if best else "",
        "status": localization["status"],
        "reason": best["reason"] if best else localization["failure_reason"],
        "synthetic_view_id": best["view_id"] if best else "",
        "synthetic_image": best_view.get("image_url", "") if best_view else "",
        "error_radius_m": localization["error_radius_m"],
        "correction_vector_m": localization["correction_vector_m"],
    }


def _task_or_404(task_id: str) -> dict:
    try:
        return get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _image_or_404(task_id: str, image_id: str) -> dict:
    for image in list_query_images(task_id):
        if image["id"] == image_id:
            return image
    for image in get_demo_data().get("vision_images", []):
        if image.get("task_id") == task_id and image.get("id") == image_id:
            return image
    raise HTTPException(status_code=404, detail=f"vision image not found: {image_id}")


def _origin(task: dict) -> list[float]:
    return task["area"]["coordinates"][0][0]


def _route_prior_pose(image: dict) -> dict:
    point = image.get("route_prior_pose") or image.get("expected_center") or [0, 0, 120]
    camera = image.get("camera", {})
    return {
        "lon": point[0],
        "lat": point[1],
        "altitude_m": point[2] if len(point) > 2 else camera.get("height_m", 120),
        "yaw_deg": camera.get("yaw_deg", 32),
        "pitch_deg": camera.get("pitch_deg", -40),
        "roll_deg": camera.get("roll_deg", 0),
    }


def _initial_pose(image: dict, route_prior: dict, origin: list[float]) -> dict:
    if image.get("initial_pose"):
        return _pose_with_defaults(image["initial_pose"])
    offset = image.get("simulated_initial_offset_m") or DEFAULT_INITIAL_OFFSETS_M.get(image["id"], [45.0, -30.0, 0.0])
    x, y = lonlat_to_xy([route_prior["lon"], route_prior["lat"]], origin)
    lon, lat = xy_to_lonlat(x + offset[0], y + offset[1], origin)
    return {
        **route_prior,
        "lon": round(lon, 9),
        "lat": round(lat, 9),
        "altitude_m": round(route_prior["altitude_m"] + (offset[2] if len(offset) > 2 else 0), 1),
    }


def _pose_with_defaults(value: dict) -> dict:
    return {
        "lon": value["lon"],
        "lat": value["lat"],
        "altitude_m": value["altitude_m"],
        "yaw_deg": value.get("yaw_deg", 0),
        "pitch_deg": value.get("pitch_deg", -45),
        "roll_deg": value.get("roll_deg", 0),
    }


def _candidate_tiles(
    task_id: str,
    image_id: str,
    tiles: list[dict],
    route_prior: dict,
    top_k: int,
    origin: list[float],
) -> list[dict]:
    tile_by_id = {tile["tile_id"]: tile for tile in tiles}
    match = get_match_result(task_id, image_id, top_k)
    selected = []
    for candidate in (match or {}).get("candidates", []):
        tile = tile_by_id.get(candidate.get("tile_id"))
        if tile and tile not in selected:
            selected.append(tile)
    if len(selected) < top_k:
        selected_ids = {tile["tile_id"] for tile in selected}
        nearest = sorted(
            [tile for tile in tiles if tile["tile_id"] not in selected_ids],
            key=lambda tile: _planar_distance([route_prior["lon"], route_prior["lat"]], tile["center"], origin),
        )
        selected.extend(nearest[: top_k - len(selected)])
    return selected[:top_k]


def _synthetic_view(
    task_id: str,
    image: dict,
    tile: dict,
    route_prior: dict,
    initial: dict,
    rank: int,
    origin: list[float],
    render_mode: str,
    lighting_options: dict | None,
) -> dict:
    center = tile["center"]
    terrain_height = _terrain_height(center)
    pose = {
        "lon": center[0],
        "lat": center[1],
        "altitude_m": round(max(initial["altitude_m"], terrain_height + image.get("camera", {}).get("height_m", 120)), 1),
        "yaw_deg": _bearing_degrees([initial["lon"], initial["lat"]], [center[0], center[1]]),
        "pitch_deg": image.get("camera", {}).get("pitch_deg", route_prior.get("pitch_deg", -40)),
        "roll_deg": route_prior.get("roll_deg", 0),
    }
    prior_distance = _planar_distance([route_prior["lon"], route_prior["lat"]], center, origin)
    image_url = tile.get("tile_image") or FALLBACK_ORTHO_IMAGE
    render_source = {
        "mode": "v0.4_ortho_tile_proxy_with_dem_building_context",
        "orthophoto": tile.get("source_image", "luojia_orthophoto"),
        "dem": "frontend/public/demo/luojia_terrain_preview.json",
        "buildings": "frontend/public/demo/luojia_buildings_preview.json",
        "note": "v0.4 returns a deterministic synthetic-view proxy; v0.5 can replace image_url with a real renderer output.",
    }
    if render_mode == "v05a":
        v05a = build_v05a_synthetic_view(
            image_url,
            f"syn_{image['id']}_{tile['tile_id']}",
            image.get("camera", {}).get("yaw_deg", pose["yaw_deg"]),
            image.get("camera", {}).get("fov_deg", 72),
            center,
            lighting_options,
        )
        image_url = v05a["image_url"]
        render_source = {
            **render_source,
            "mode": v05a["mode"],
            "v05a": v05a,
            "note": "v0.5a rotates the orthophoto tile by UAV yaw and center-crops/scales by camera FOV; DEM/building data remain metadata context.",
        }
    return {
        "view_id": f"syn_{image['id']}_{tile['tile_id']}",
        "task_id": task_id,
        "image_id": image["id"],
        "tile_id": tile["tile_id"],
        "image_url": image_url,
        "pose": pose,
        "bbox": tile["bbox"],
        "terrain_height_m": terrain_height,
        "building_count": _building_count(tile["bbox"]),
        "render_source": render_source,
        "score_prior": round(max(0.1, min(1.0, 1 - prior_distance / 650)), 3),
        "rank": rank,
    }


def _estimated_pose_from_candidate(candidate: dict, view: dict) -> dict:
    center = candidate.get("center") or view["pose"]
    return {
        "lon": center[0],
        "lat": center[1],
        "altitude_m": center[2] if len(center) > 2 else view["pose"]["altitude_m"],
        "yaw_deg": view["pose"]["yaw_deg"],
        "pitch_deg": view["pose"]["pitch_deg"],
        "roll_deg": view["pose"]["roll_deg"],
    }


def _correction_vector_m(initial_pose: dict, estimated_pose: dict, origin: list[float]) -> list[float]:
    ix, iy = lonlat_to_xy([initial_pose["lon"], initial_pose["lat"]], origin)
    ex, ey = lonlat_to_xy([estimated_pose["lon"], estimated_pose["lat"]], origin)
    return [
        round(ex - ix, 1),
        round(ey - iy, 1),
        round(estimated_pose["altitude_m"] - initial_pose["altitude_m"], 1),
    ]


def _planar_distance(a: list[float], b: list[float], origin: list[float]) -> float:
    ax, ay = lonlat_to_xy(a, origin)
    bx, by = lonlat_to_xy(b, origin)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _status_for_confidence(confidence: float, candidate_status: str) -> str:
    if candidate_status == "best" and confidence >= 0.5:
        return "best"
    if confidence >= 0.5:
        return "candidate"
    return "needs_review"


def _failure_reason(candidate: dict, confidence: float) -> str:
    if confidence < 0.5:
        return candidate.get("reason") or "synthetic view match confidence is below navigation threshold"
    return ""


def _error_radius_m(confidence: float, inlier_ratio: float) -> float:
    return round(max(8.0, 95.0 * (1 - confidence) + 35.0 * (1 - inlier_ratio)), 1)


def _navigation_effect(status: str, best: dict | None) -> str:
    if status == "localized" and best:
        return "visual observation can correct the simulated navigation state toward the estimated pose"
    if status == "needs_review":
        return "visual observation is retained for review and does not directly correct the simulated navigation state"
    return "no reliable visual observation is available"


def _localization_failure_reason(best: dict | None) -> str:
    if not best:
        return "no synthetic-view match candidate was produced"
    if best["confidence"] < 0.5:
        return best.get("failure_reason") or "best synthetic-view match confidence is below threshold"
    return ""


def _view_for_match(localization: dict, match: dict | None) -> dict | None:
    if not match:
        return None
    for view in localization.get("synthetic_views", []):
        if view["view_id"] == match["view_id"]:
            return view
    return None


def _match_result_from_synthetic_views(response: dict) -> dict:
    candidates = []
    auto_route_frame = str(response.get("image_id", "")).startswith("auto_uav_")
    for view in response.get("synthetic_views", []):
        confidence = max(0.42, min(0.9, view.get("score_prior", 0.55) + 0.12 - (view["rank"] - 1) * 0.06))
        center = [view["pose"]["lon"], view["pose"]["lat"], view["pose"]["altitude_m"]]
        offset = [round((1 - confidence) * 38, 1), round((view["rank"] - 1) * -14.0, 1)]
        reason = f"{view['view_id']} generated from route-distance/key-change automatic frame selection"
        if auto_route_frame:
            confidence = max(confidence, 0.78 - (view["rank"] - 1) * 0.09)
            reason = f"{view['view_id']} route-bound DEM/orthophoto frame aligned with current planned trajectory"
        if response.get("frame_trigger") == "route_arrival":
            confidence = max(0.5, 0.88 - (view["rank"] - 1) * 0.08)
            center = [
                response["route_prior_pose"]["lon"],
                response["route_prior_pose"]["lat"],
                response["route_prior_pose"]["altitude_m"],
            ]
            offset = [0.0, 0.0]
            reason = "terminal landing correction from DEM/orthophoto synthetic-view alignment"
        candidates.append(
            {
                "tile_id": view["tile_id"],
                "confidence": round(confidence, 2),
                "matched_points": round(128 * confidence + 18),
                "inlier_ratio": round(max(0.22, confidence - 0.15), 2),
                "bbox": view["bbox"],
                "center": center,
                "offset_m": offset,
                "status": "best" if view["rank"] == 1 and confidence >= 0.5 else "candidate" if confidence >= 0.5 else "needs_review",
                "reason": reason,
            }
        )
    return {
        "match_id": f"match_{response['image_id']}_synthetic_auto",
        "task_id": response["task_id"],
        "image_id": response["image_id"],
        "query_image": response["query_image"],
        "provider": "synthetic_view_route_proxy",
        "status": "completed" if candidates else "failed",
        "algorithm_trace": PIPELINE,
        "candidates": candidates,
    }


@lru_cache(maxsize=1)
def _terrain_vertices() -> list[dict]:
    if not TERRAIN_PREVIEW.exists():
        return []
    return json.loads(TERRAIN_PREVIEW.read_text(encoding="utf-8")).get("vertices", [])


def _terrain_height(point: list[float]) -> float:
    vertices = _terrain_vertices()
    if not vertices:
        return 0.0
    lon, lat = point[0], point[1]
    nearest = min(vertices, key=lambda vertex: (vertex["lon"] - lon) ** 2 + (vertex["lat"] - lat) ** 2)
    return round(float(nearest.get("height_m", 0.0)), 2)


@lru_cache(maxsize=1)
def _building_polygons() -> list[dict]:
    if not BUILDINGS_PREVIEW.exists():
        return []
    return json.loads(BUILDINGS_PREVIEW.read_text(encoding="utf-8")).get("buildings", [])


def _building_count(bbox: list[list[float]]) -> int:
    count = 0
    for building in _building_polygons():
        center = _centroid(building.get("polygon", []))
        if center and point_in_polygon(center, bbox):
            count += 1
    return count


def _centroid(points: list[list[float]]) -> list[float] | None:
    if not points:
        return None
    usable = points[:-1] if points[0] == points[-1] else points
    return [
        sum(point[0] for point in usable) / len(usable),
        sum(point[1] for point in usable) / len(usable),
    ]


def _bearing_degrees(start: list[float], end: list[float]) -> float:
    lon1 = start[0] * pi / 180
    lon2 = end[0] * pi / 180
    lat1 = start[1] * pi / 180
    lat2 = end[1] * pi / 180
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    return round((atan2(y, x) * 180 / pi + 360) % 360, 1)
