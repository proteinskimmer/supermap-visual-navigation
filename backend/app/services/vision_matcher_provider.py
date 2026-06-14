from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime
from functools import lru_cache
from importlib.util import find_spec
from math import asin, atan2, cos, degrees, radians, sin, tan
from pathlib import Path
from uuid import uuid4

from app.services.geometry import lonlat_to_xy, xy_to_lonlat


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_DEMO_ROOT = PROJECT_ROOT / "frontend" / "public" / "demo"
SEMI_REAL_UAV_FRAME_DIR = PUBLIC_DEMO_ROOT / "uav_frames"
V05_SYNTHETIC_VIEW_DIR = PUBLIC_DEMO_ROOT / "synthetic_views"
V05_EVIDENCE_DIR = PROJECT_ROOT / "demo_data" / "generated" / "v05_match_evidence"

PRECOMPUTED_MATCHER_MODES = {"synthetic_v04", "precomputed", "precomputed_proxy"}
REAL_MATCHER_MODES = {"opencv_orb", "opencv_sift", "external_deep_matcher"}
SUPPORTED_MATCHER_MODES = PRECOMPUTED_MATCHER_MODES | REAL_MATCHER_MODES
DEFAULT_CAMERA_CALIBRATION = {
    "model": "pinhole_plumb_bob",
    "width_px": 1280,
    "height_px": 720,
    "fx": 960.0,
    "fy": 960.0,
    "cx": 640.0,
    "cy": 360.0,
    "distortion_model": "plumb_bob",
    "distortion_coefficients": {
        "k1": -0.045,
        "k2": 0.012,
        "p1": 0.0008,
        "p2": -0.0006,
        "k3": 0.0,
    },
    "source": "semi_real_uav_frame_simulation",
    "note": "Simulated lens model recorded for later geometric/PnP solving; values are controlled demo parameters, not a calibrated real UAV camera.",
}
DEFAULT_LIGHTING_OPTIONS = {
    "enabled": True,
    "capture_datetime": "2026-06-09T10:30:00+08:00",
    "timezone_offset_hours": 8,
    "exposure_ev": 0.0,
    "shadow_strength": 0.22,
    "haze": 0.08,
    "color_temperature_k": 5600,
    "note": "Semi-real lighting parameters are controllable demo inputs for feature sensitivity analysis, not measured irradiance.",
}


def normalize_matcher_mode(mode: str | None) -> str:
    normalized = (mode or "synthetic_v04").strip().lower()
    if normalized == "synthetic_v04":
        return "precomputed_proxy"
    if normalized == "precomputed":
        return "precomputed_proxy"
    return normalized


def is_precomputed_matcher(mode: str | None) -> bool:
    return normalize_matcher_mode(mode) in PRECOMPUTED_MATCHER_MODES


def is_supported_matcher(mode: str | None) -> bool:
    return normalize_matcher_mode(mode) in SUPPORTED_MATCHER_MODES


def provider_name(mode: str | None) -> str:
    normalized = normalize_matcher_mode(mode)
    if normalized == "precomputed_proxy":
        return "synthetic_view_v04_precomputed_proxy"
    if normalized in {"opencv_orb", "opencv_sift"}:
        return normalized
    return "external_deep_matcher"


def matcher_runtime_status() -> dict:
    cv2 = _opencv_status()
    return {
        "precomputed_proxy": {
            "status": "available",
            "provider": "synthetic_view_v04_precomputed_proxy",
            "description": "Stable v0.4 proxy matcher backed by generated synthetic-view candidates.",
        },
        "opencv_orb": {
            "status": "available" if cv2["available"] and cv2["has_orb"] else "unavailable",
            "provider": "opencv_orb",
            "cv2_available": cv2["available"],
            "cv2_version": cv2["version"],
            "algorithm_available": cv2["has_orb"],
            "description": "v0.5a OpenCV ORB + BFMatcher/Hamming + RANSAC provider.",
        },
        "opencv_sift": {
            "status": "planned" if cv2["available"] and cv2["has_sift"] else "unavailable",
            "provider": "opencv_sift",
            "cv2_available": cv2["available"],
            "cv2_version": cv2["version"],
            "algorithm_available": cv2["has_sift"],
            "description": "Optional v0.5 provider; OpenCV SIFT is detected but not wired into navigation yet.",
        },
        "external_deep_matcher": {
            "status": "planned",
            "provider": "external_deep_matcher",
            "description": "Reserved adapter for LoFTR/LightGlue/DINO-style external matchers.",
        },
    }


def unavailable_reason(mode: str | None) -> str:
    normalized = normalize_matcher_mode(mode)
    if normalized in {"opencv_orb", "opencv_sift"}:
        cv2 = _opencv_status()
        if not cv2["available"]:
            return "OpenCV cv2 is not installed in the current supermap_nav environment."
        if normalized == "opencv_orb" and not cv2["has_orb"]:
            return "OpenCV is installed, but ORB_create is not available."
        if normalized == "opencv_sift" and not cv2["has_sift"]:
            return "OpenCV is installed, but SIFT_create is not available."
        if normalized == "opencv_sift":
            return "opencv_sift provider is reserved for a later v0.5 step."
        return ""
    if normalized == "external_deep_matcher":
        return "External deep matcher provider is reserved for v0.5 integration."
    return f"Unsupported matcher mode: {mode}"


def default_camera_calibration() -> dict:
    return json.loads(json.dumps(DEFAULT_CAMERA_CALIBRATION))


def default_lighting_options() -> dict:
    return json.loads(json.dumps(DEFAULT_LIGHTING_OPTIONS))


def build_semi_real_uav_frame(
    tile_image_url: str,
    frame_id: str,
    yaw_deg: float,
    fov_deg: float,
    geo_point: list[float],
    lighting_options: dict | None = None,
) -> dict:
    lighting = _normalize_lighting(lighting_options, geo_point)
    source_path = _resolve_demo_path(tile_image_url)
    output_name = f"semi_real_{_safe_id(frame_id)}_{_lighting_key(lighting)}.png"
    output_path = SEMI_REAL_UAV_FRAME_DIR / output_name
    output_url = f"/demo/uav_frames/{output_name}"
    calibration = default_camera_calibration()
    cv2_status = _opencv_status()
    if not cv2_status["available"] or not source_path.exists():
        return {
            "image_url": tile_image_url,
            "image_path": str(source_path),
            "mode": "source_ortho_tile_fallback",
            "available": False,
            "camera_calibration": calibration,
            "lighting_model": lighting,
            "failure_reason": unavailable_reason("opencv_orb") if not cv2_status["available"] else f"source image not found: {tile_image_url}",
        }

    import cv2  # type: ignore
    import numpy as np  # type: ignore

    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        return {
            "image_url": tile_image_url,
            "image_path": str(source_path),
            "mode": "source_ortho_tile_fallback",
            "available": False,
            "camera_calibration": calibration,
            "lighting_model": lighting,
            "failure_reason": f"OpenCV could not read source image: {tile_image_url}",
        }

    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    rotation = cv2.getRotationMatrix2D(center, -float(yaw_deg) * 0.92, 1.0)
    rotated = cv2.warpAffine(image, rotation, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    crop_ratio = max(0.48, min(0.88, 72.0 / max(float(fov_deg), 1.0) * 0.66))
    crop_w = max(32, int(w * crop_ratio))
    crop_h = max(32, int(h * crop_ratio * 9 / 16))
    crop_h = min(crop_h, h)
    x0 = max(0, (w - crop_w) // 2)
    y0 = max(0, (h - crop_h) // 2)
    cropped = rotated[y0 : y0 + crop_h, x0 : x0 + crop_w]
    resized = cv2.resize(cropped, (calibration["width_px"], calibration["height_px"]), interpolation=cv2.INTER_LINEAR)

    camera_matrix = np.array(
        [[calibration["fx"], 0, calibration["cx"]], [0, calibration["fy"], calibration["cy"]], [0, 0, 1]],
        dtype=np.float32,
    )
    coeffs = calibration["distortion_coefficients"]
    distortion = np.array([coeffs["k1"], coeffs["k2"], coeffs["p1"], coeffs["p2"], coeffs["k3"]], dtype=np.float32)
    lit = _apply_lighting(resized, lighting)
    distorted = cv2.undistort(lit, camera_matrix, -distortion)
    yy, xx = np.indices((calibration["height_px"], calibration["width_px"]))
    radius = np.sqrt(((xx - calibration["cx"]) / calibration["cx"]) ** 2 + ((yy - calibration["cy"]) / calibration["cy"]) ** 2)
    vignette = np.clip(1.0 - 0.22 * radius**2, 0.72, 1.0)
    semi_real = np.clip(distorted.astype(np.float32) * vignette[..., None], 0, 255).astype(np.uint8)

    SEMI_REAL_UAV_FRAME_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_cv2_imwrite(output_path, semi_real)
    return {
        "image_url": output_url,
        "image_path": str(output_path),
        "mode": "semi_real_ortho_tile_yaw_crop_distorted",
        "available": True,
        "source_image": str(source_path),
        "yaw_deg": round(float(yaw_deg), 2),
        "fov_deg": round(float(fov_deg), 2),
        "crop_ratio": round(crop_ratio, 3),
        "camera_calibration": calibration,
        "lighting_model": lighting,
    }


def build_v05a_synthetic_view(
    tile_image_url: str,
    view_id: str,
    yaw_deg: float,
    fov_deg: float,
    geo_point: list[float],
    lighting_options: dict | None = None,
) -> dict:
    lighting = _normalize_lighting(lighting_options, geo_point)
    source_path = _resolve_demo_path(tile_image_url)
    output_name = f"v05a_{_safe_id(view_id)}_{_lighting_key(lighting)}.png"
    output_path = V05_SYNTHETIC_VIEW_DIR / output_name
    output_url = f"/demo/synthetic_views/{output_name}"
    cv2_status = _opencv_status()
    if not cv2_status["available"] or not source_path.exists():
        return {
            "image_url": tile_image_url,
            "image_path": str(source_path),
            "mode": "v0.4_ortho_tile_proxy_with_dem_building_context",
            "available": False,
            "lighting_model": lighting,
            "failure_reason": unavailable_reason("opencv_orb") if not cv2_status["available"] else f"source image not found: {tile_image_url}",
        }

    import cv2  # type: ignore

    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        return {
            "image_url": tile_image_url,
            "image_path": str(source_path),
            "mode": "v0.4_ortho_tile_proxy_with_dem_building_context",
            "available": False,
            "lighting_model": lighting,
            "failure_reason": f"OpenCV could not read source image: {tile_image_url}",
        }

    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    rotation = cv2.getRotationMatrix2D(center, -float(yaw_deg), 1.0)
    rotated = cv2.warpAffine(image, rotation, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    crop_ratio = max(0.52, min(0.92, 72.0 / max(float(fov_deg), 1.0) * 0.72))
    crop_w = max(32, int(w * crop_ratio))
    crop_h = max(32, int(crop_w * 9 / 16))
    crop_h = min(crop_h, h)
    x0 = max(0, (w - crop_w) // 2)
    y0 = max(0, (h - crop_h) // 2)
    cropped = rotated[y0 : y0 + crop_h, x0 : x0 + crop_w]
    projected = cv2.resize(cropped, (DEFAULT_CAMERA_CALIBRATION["width_px"], DEFAULT_CAMERA_CALIBRATION["height_px"]), interpolation=cv2.INTER_LINEAR)
    projected = _apply_lighting(projected, lighting)
    V05_SYNTHETIC_VIEW_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_cv2_imwrite(output_path, projected)
    return {
        "image_url": output_url,
        "image_path": str(output_path),
        "mode": "v0.5a_ortho_tile_yaw_crop_scale_with_dem_building_metadata",
        "available": True,
        "source_image": str(source_path),
        "yaw_deg": round(float(yaw_deg), 2),
        "fov_deg": round(float(fov_deg), 2),
        "crop_ratio": round(crop_ratio, 3),
        "lighting_model": lighting,
    }


def localize_with_opencv_orb(task_id: str, image_id: str, response: dict, origin: list[float]) -> dict:
    cv2_status = _opencv_status()
    if not cv2_status["available"] or not cv2_status["has_orb"]:
        return unavailable_localization(task_id, image_id, response, "opencv_orb")

    matches = []
    for view in response.get("synthetic_views", []):
        match = _match_orb_pair(response["query_image"], view, response, origin)
        matches.append(match)

    matches.sort(key=lambda item: (item["confidence"], item["inlier_ratio"], item["matched_points"]), reverse=True)
    for rank, item in enumerate(matches, start=1):
        item["rank"] = rank

    best = matches[0] if matches else None
    status = "localized" if best and best["confidence"] >= 0.5 else "needs_review" if best and best["matched_points"] else "failed"
    return {
        "localization_id": f"loc_{image_id}_opencv_orb_v05a",
        "task_id": task_id,
        "image_id": image_id,
        "query_image": response["query_image"],
        "provider": "opencv_orb",
        "status": status,
        "image_simulation": response.get("image_simulation", {}),
        "initial_pose": response["initial_pose"],
        "route_prior_pose": response["route_prior_pose"],
        "best_estimated_pose": best["estimated_pose"] if best and best["confidence"] >= 0.5 else None,
        "confidence": best["confidence"] if best else 0,
        "error_radius_m": best["error_radius_m"] if best else 999,
        "matched_points": best["matched_points"] if best else 0,
        "inlier_ratio": best["inlier_ratio"] if best else 0,
        "correction_vector_m": best["correction_vector_m"] if best and best["confidence"] >= 0.5 else [0.0, 0.0, 0.0],
        "synthetic_views": response["synthetic_views"],
        "matches": matches,
        "navigation_effect": _navigation_effect(status),
        "failure_reason": "" if status == "localized" else (best["failure_reason"] if best else "no synthetic-view candidates were available"),
        "pipeline": [
            *response.get("pipeline", []),
            "opencv_orb_keypoints",
            "bfmatcher_hamming_ratio_test",
            "ransac_homography",
            "pixel_offset_to_map_pose",
            "v05_match_evidence",
        ],
    }


def unavailable_localization(task_id: str, image_id: str, response: dict, matcher_mode: str) -> dict:
    reason = unavailable_reason(matcher_mode)
    return {
        "localization_id": f"loc_{image_id}_{matcher_mode}_v05_unavailable",
        "task_id": task_id,
        "image_id": image_id,
        "query_image": response["query_image"],
        "provider": f"{provider_name(matcher_mode)}_unavailable",
        "status": "failed",
        "image_simulation": response.get("image_simulation", {}),
        "initial_pose": response["initial_pose"],
        "route_prior_pose": response["route_prior_pose"],
        "best_estimated_pose": None,
        "confidence": 0,
        "error_radius_m": 999,
        "matched_points": 0,
        "inlier_ratio": 0,
        "correction_vector_m": [0.0, 0.0, 0.0],
        "synthetic_views": response["synthetic_views"],
        "matches": [],
        "navigation_effect": "real matcher provider is unavailable; navigation must keep the v0.4 proxy or wait for review",
        "failure_reason": reason,
        "pipeline": [*response.get("pipeline", []), f"{matcher_mode}_provider_unavailable"],
    }


def _match_orb_pair(query_url: str, view: dict, response: dict, origin: list[float]) -> dict:
    import cv2  # type: ignore

    query_path = _resolve_demo_path(query_url)
    train_path = _resolve_demo_path(view["image_url"])
    base = f"{_safe_id(response['image_id'])}_{_safe_id(view['tile_id'])}_opencv_orb"
    evidence = _evidence_paths(base)
    failure_reason = ""

    query = cv2.imread(str(query_path), cv2.IMREAD_COLOR)
    train = cv2.imread(str(train_path), cv2.IMREAD_COLOR)
    if query is None or train is None:
        failure_reason = f"OpenCV could not read query or synthetic view image: {query_url}, {view['image_url']}"
        return _failed_match(view, response, origin, evidence, failure_reason)

    _write_evidence_inputs(query_path, train_path, evidence)
    query_gray = cv2.cvtColor(query, cv2.COLOR_BGR2GRAY)
    train_gray = cv2.cvtColor(train, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=1600, scaleFactor=1.2, nlevels=8)
    kp_query, desc_query = orb.detectAndCompute(query_gray, None)
    kp_train, desc_train = orb.detectAndCompute(train_gray, None)
    if desc_query is None or desc_train is None or len(kp_query) < 8 or len(kp_train) < 8:
        failure_reason = f"not enough ORB features: query={len(kp_query)}, synthetic={len(kp_train)}"
        _write_match_images(query, kp_query, train, kp_train, [], [], evidence)
        return _failed_match(view, response, origin, evidence, failure_reason)

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    raw_matches = matcher.knnMatch(desc_query, desc_train, k=2)
    good = []
    for pair in raw_matches:
        if len(pair) < 2:
            continue
        first, second = pair
        if first.distance < 0.88 * second.distance:
            good.append(first)
    if len(good) < 8:
        failure_reason = f"not enough ratio-test matches: {len(good)}"
        _write_match_images(query, kp_query, train, kp_train, good, [], evidence)
        return _failed_match(view, response, origin, evidence, failure_reason, matched_points=len(good))

    src = _np_array([kp_query[item.queryIdx].pt for item in good])
    dst = _np_array([kp_train[item.trainIdx].pt for item in good])
    homography, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    inliers = [match for match, keep in zip(good, mask.ravel().tolist() if mask is not None else []) if keep]
    if homography is None or len(inliers) < 6:
        failure_reason = f"RANSAC could not estimate a stable homography: inliers={len(inliers)}"
        _write_match_images(query, kp_query, train, kp_train, good, inliers, evidence)
        return _failed_match(view, response, origin, evidence, failure_reason, matched_points=len(good), inlier_ratio=_safe_ratio(len(inliers), len(good)))

    offset_px = _homography_center_offset(homography, query.shape, train.shape)
    offset_m = _pixel_offset_to_meters(offset_px, train.shape, view, origin)
    estimated_pose = _estimated_pose_from_offset(response["route_prior_pose"], view["pose"], offset_m, origin)
    correction = _correction_vector(response["initial_pose"], estimated_pose, origin)
    inlier_ratio = _safe_ratio(len(inliers), len(good))
    confidence = _confidence(len(good), inlier_ratio)
    error_radius = _error_radius(confidence, inlier_ratio, len(good))
    status = "best" if confidence >= 0.5 else "needs_review"
    failure_reason = "" if confidence >= 0.5 else "ORB/RANSAC confidence is below navigation threshold"
    _write_match_images(query, kp_query, train, kp_train, good, inliers, evidence)
    result = {
        "view_id": view["view_id"],
        "tile_id": view["tile_id"],
        "confidence": confidence,
        "matched_points": len(good),
        "inlier_ratio": inlier_ratio,
        "offset_m": offset_m,
        "correction_vector_m": correction,
        "error_radius_m": error_radius,
        "estimated_pose": estimated_pose,
        "status": status,
        "failure_reason": failure_reason,
        "reason": "OpenCV ORB descriptors matched against v0.5a synthetic view; RANSAC homography converted image-center offset to map pose.",
        "evidence": _evidence_payload(evidence),
        "rank": 1,
    }
    _write_result_json(evidence["json"], response, view, result)
    return result


def _failed_match(
    view: dict,
    response: dict,
    origin: list[float],
    evidence: dict[str, Path],
    failure_reason: str,
    matched_points: int = 0,
    inlier_ratio: float = 0.0,
) -> dict:
    estimated_pose = view["pose"]
    result = {
        "view_id": view["view_id"],
        "tile_id": view["tile_id"],
        "confidence": 0.0,
        "matched_points": matched_points,
        "inlier_ratio": round(inlier_ratio, 3),
        "offset_m": [0.0, 0.0],
        "correction_vector_m": _correction_vector(response["initial_pose"], estimated_pose, origin),
        "error_radius_m": 999,
        "estimated_pose": estimated_pose,
        "status": "failed",
        "failure_reason": failure_reason,
        "reason": "OpenCV ORB provider failed before producing a navigation-grade pose.",
        "evidence": _evidence_payload(evidence),
        "rank": 1,
    }
    _write_result_json(evidence["json"], response, view, result)
    return result


def _resolve_demo_path(url_or_path: str) -> Path:
    value = url_or_path.replace("\\", "/")
    if value.startswith("/demo/"):
        return PUBLIC_DEMO_ROOT / value.removeprefix("/demo/")
    path = Path(url_or_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _evidence_paths(base: str) -> dict[str, Path]:
    V05_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "uav": V05_EVIDENCE_DIR / f"{base}_uav.png",
        "synthetic": V05_EVIDENCE_DIR / f"{base}_synthetic.png",
        "matches": V05_EVIDENCE_DIR / f"{base}_matches.png",
        "inliers": V05_EVIDENCE_DIR / f"{base}_inliers.png",
        "json": V05_EVIDENCE_DIR / f"{base}_result.json",
    }


def _write_evidence_inputs(query_path: Path, train_path: Path, evidence: dict[str, Path]) -> None:
    if query_path.exists():
        _atomic_copyfile(query_path, evidence["uav"])
    if train_path.exists():
        _atomic_copyfile(train_path, evidence["synthetic"])


def _write_match_images(query, kp_query, train, kp_train, matches, inliers, evidence: dict[str, Path]) -> None:
    import cv2  # type: ignore

    if matches:
        _atomic_cv2_imwrite(evidence["matches"], cv2.drawMatches(query, kp_query, train, kp_train, matches[:80], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS))
    else:
        _atomic_cv2_imwrite(evidence["matches"], _side_by_side_placeholder(query, train, "No ORB ratio-test matches"))
    if inliers:
        _atomic_cv2_imwrite(evidence["inliers"], cv2.drawMatches(query, kp_query, train, kp_train, inliers[:80], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS))
    else:
        _atomic_cv2_imwrite(evidence["inliers"], _side_by_side_placeholder(query, train, "No RANSAC inliers"))


def _side_by_side_placeholder(query, train, label: str):
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    height = max(query.shape[0], train.shape[0])
    width = query.shape[1] + train.shape[1]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[: query.shape[0], : query.shape[1]] = query
    canvas[: train.shape[0], query.shape[1] : query.shape[1] + train.shape[1]] = train
    cv2.putText(canvas, label, (24, min(height - 24, 48)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
    return canvas


def _write_result_json(path: Path, response: dict, view: dict, result: dict) -> None:
    payload = {
        "image_id": response["image_id"],
        "tile_id": view["tile_id"],
        "provider": "opencv_orb",
        "matched_points": result["matched_points"],
        "inlier_ratio": result["inlier_ratio"],
        "confidence": result["confidence"],
        "error_radius_m": result["error_radius_m"],
        "offset_m": result["offset_m"],
        "estimated_pose": result["estimated_pose"],
        "failure_reason": result["failure_reason"],
        "view_id": view["view_id"],
        "synthetic_image": view["image_url"],
        "evidence_files": result.get("evidence", {}).get("files", {}),
        "evidence_urls": result.get("evidence", {}).get("urls", {}),
    }
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _atomic_cv2_imwrite(path: Path, image) -> None:
    import cv2  # type: ignore

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    ok = cv2.imwrite(str(tmp_path), image)
    if not ok:
        raise OSError(f"OpenCV failed to write image: {path}")
    _replace_when_available(tmp_path, path)


def _atomic_copyfile(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(target)
    shutil.copyfile(source, tmp_path)
    _replace_when_available(tmp_path, target)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    tmp_path.write_text(text, encoding="utf-8")
    _replace_when_available(tmp_path, path)


def _tmp_path(path: Path) -> Path:
    return path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}.tmp{path.suffix}")


def _replace_when_available(tmp_path: Path, target_path: Path) -> None:
    for _ in range(20):
        try:
            os.replace(tmp_path, target_path)
            return
        except PermissionError:
            time.sleep(0.05)
    if target_path.exists() and target_path.stat().st_size > 0:
        tmp_path.unlink(missing_ok=True)
        return
    os.replace(tmp_path, target_path)


def _normalize_lighting(options: dict | None, geo_point: list[float]) -> dict:
    lighting = default_lighting_options()
    if options:
        for key in ["enabled", "capture_datetime", "timezone_offset_hours", "exposure_ev", "shadow_strength", "haze", "color_temperature_k"]:
            if key in options and options[key] is not None:
                lighting[key] = options[key]
        for key in ["sun_azimuth_deg", "sun_elevation_deg"]:
            if key in options and options[key] is not None:
                lighting[key] = options[key]

    lon = float(geo_point[0])
    lat = float(geo_point[1])
    lighting["longitude_deg"] = round(lon, 9)
    lighting["latitude_deg"] = round(lat, 9)
    if "sun_azimuth_deg" not in lighting or "sun_elevation_deg" not in lighting:
        sun = _solar_position(lighting["capture_datetime"], lat, lon, float(lighting.get("timezone_offset_hours", 8)))
        lighting["sun_azimuth_deg"] = sun["sun_azimuth_deg"]
        lighting["sun_elevation_deg"] = sun["sun_elevation_deg"]

    lighting["exposure_ev"] = round(max(-2.0, min(2.0, float(lighting.get("exposure_ev", 0.0)))), 2)
    lighting["shadow_strength"] = round(max(0.0, min(0.75, float(lighting.get("shadow_strength", 0.22)))), 2)
    lighting["haze"] = round(max(0.0, min(0.6, float(lighting.get("haze", 0.08)))), 2)
    lighting["color_temperature_k"] = int(max(3200, min(8500, int(lighting.get("color_temperature_k", 5600)))))
    lighting["timezone_offset_hours"] = round(max(-12.0, min(14.0, float(lighting.get("timezone_offset_hours", 8)))), 1)
    lighting["enabled"] = bool(lighting.get("enabled", True))
    return lighting


def _solar_position(capture_datetime: str, latitude_deg: float, longitude_deg: float, timezone_offset_hours: float) -> dict:
    dt = datetime.fromisoformat(capture_datetime.replace("Z", "+00:00"))
    day = dt.timetuple().tm_yday
    hour = dt.hour + dt.minute / 60 + dt.second / 3600
    tz_offset = (dt.utcoffset().total_seconds() / 3600) if dt.utcoffset() else timezone_offset_hours
    gamma = 2.0 * 3.141592653589793 * (day - 1 + (hour - 12) / 24) / 365.0
    declination = (
        0.006918
        - 0.399912 * cos(gamma)
        + 0.070257 * sin(gamma)
        - 0.006758 * cos(2 * gamma)
        + 0.000907 * sin(2 * gamma)
        - 0.002697 * cos(3 * gamma)
        + 0.00148 * sin(3 * gamma)
    )
    equation_time = 229.18 * (
        0.000075
        + 0.001868 * cos(gamma)
        - 0.032077 * sin(gamma)
        - 0.014615 * cos(2 * gamma)
        - 0.040849 * sin(2 * gamma)
    )
    time_offset = equation_time + 4.0 * longitude_deg - 60.0 * tz_offset
    true_solar_time = (hour * 60.0 + time_offset) % 1440.0
    hour_angle = radians(true_solar_time / 4.0 - 180.0)
    latitude = radians(latitude_deg)
    elevation = asin(sin(latitude) * sin(declination) + cos(latitude) * cos(declination) * cos(hour_angle))
    azimuth = atan2(
        sin(hour_angle),
        cos(hour_angle) * sin(latitude) - tan(declination) * cos(latitude),
    )
    return {
        "sun_elevation_deg": round(degrees(elevation), 2),
        "sun_azimuth_deg": round((degrees(azimuth) + 180.0) % 360.0, 2),
    }


def _apply_lighting(image, lighting: dict):
    if not lighting.get("enabled", True):
        return image
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    img = image.astype(np.float32)
    exposure = 2 ** float(lighting.get("exposure_ev", 0.0))
    elevation = max(0.0, min(90.0, float(lighting.get("sun_elevation_deg", 45.0))))
    azimuth = radians(float(lighting.get("sun_azimuth_deg", 135.0)))
    shadow = float(lighting.get("shadow_strength", 0.2)) * (1.0 - elevation / 90.0)
    haze = float(lighting.get("haze", 0.08))
    temp = float(lighting.get("color_temperature_k", 5600))

    yy, xx = np.indices(img.shape[:2])
    x = (xx / max(img.shape[1] - 1, 1)) - 0.5
    y = (yy / max(img.shape[0] - 1, 1)) - 0.5
    direction = np.cos(azimuth) * x + np.sin(azimuth) * y
    directional = 1.0 + 0.24 * (elevation / 90.0) * direction - shadow * np.clip(-direction, 0, 1)
    img *= directional[..., None] * exposure

    if temp < 5600:
        warm = (5600 - temp) / 2400
        img[..., 2] *= 1.0 + 0.12 * warm
        img[..., 0] *= 1.0 - 0.08 * warm
    else:
        cool = (temp - 5600) / 2900
        img[..., 0] *= 1.0 + 0.10 * cool
        img[..., 2] *= 1.0 - 0.06 * cool

    if haze:
        veil = np.full_like(img, 220.0)
        img = img * (1.0 - haze) + veil * haze
        img = cv2.GaussianBlur(img, (0, 0), sigmaX=0.45 + haze * 1.6)

    return np.clip(img, 0, 255).astype(np.uint8)


def _lighting_key(lighting: dict) -> str:
    return (
        f"lat{float(lighting.get('latitude_deg', 0)):.4f}_lon{float(lighting.get('longitude_deg', 0)):.4f}_"
        f"az{float(lighting.get('sun_azimuth_deg', 0)):.0f}_el{float(lighting.get('sun_elevation_deg', 0)):.0f}_"
        f"ev{float(lighting.get('exposure_ev', 0)):+.1f}_sh{float(lighting.get('shadow_strength', 0)):.2f}_"
        f"hz{float(lighting.get('haze', 0)):.2f}_k{int(lighting.get('color_temperature_k', 5600))}"
    ).replace("+", "p").replace("-", "m").replace(".", "d")


def _evidence_payload(evidence: dict[str, Path]) -> dict:
    files = {
        "uav_image": str(evidence["uav"]),
        "synthetic_image": str(evidence["synthetic"]),
        "match_lines": str(evidence["matches"]),
        "ransac_inliers": str(evidence["inliers"]),
        "result_json": str(evidence["json"]),
    }
    urls = {key: f"/api/vision/evidence/{Path(value).name}" for key, value in files.items()}
    return {"files": files, "urls": urls}


def _np_array(points: list[tuple[float, float]]):
    import numpy as np  # type: ignore

    return np.float32(points).reshape(-1, 1, 2)


def _homography_center_offset(homography, query_shape, train_shape) -> list[float]:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    qh, qw = query_shape[:2]
    th, tw = train_shape[:2]
    center = np.float32([[[qw / 2, qh / 2]]])
    projected = cv2.perspectiveTransform(center, homography)[0][0]
    return [round(float(projected[0] - tw / 2), 3), round(float(projected[1] - th / 2), 3)]


def _pixel_offset_to_meters(offset_px: list[float], image_shape, view: dict, origin: list[float]) -> list[float]:
    h, w = image_shape[:2]
    bbox = view["bbox"]
    xs = [lonlat_to_xy(point, origin)[0] for point in bbox]
    ys = [lonlat_to_xy(point, origin)[1] for point in bbox]
    meters_per_px_x = (max(xs) - min(xs)) / max(w, 1)
    meters_per_px_y = (max(ys) - min(ys)) / max(h, 1)
    return [round(offset_px[0] * meters_per_px_x, 1), round(-offset_px[1] * meters_per_px_y, 1)]


def _estimated_pose_from_offset(route_prior_pose: dict, view_pose: dict, offset_m: list[float], origin: list[float]) -> dict:
    x, y = lonlat_to_xy([view_pose["lon"], view_pose["lat"]], origin)
    lon, lat = xy_to_lonlat(x + offset_m[0], y + offset_m[1], origin)
    return {
        "lon": round(lon, 9),
        "lat": round(lat, 9),
        "altitude_m": route_prior_pose["altitude_m"],
        "yaw_deg": route_prior_pose.get("yaw_deg", view_pose.get("yaw_deg", 0)),
        "pitch_deg": route_prior_pose.get("pitch_deg", view_pose.get("pitch_deg", -40)),
        "roll_deg": route_prior_pose.get("roll_deg", view_pose.get("roll_deg", 0)),
    }


def _correction_vector(initial_pose: dict, estimated_pose: dict, origin: list[float]) -> list[float]:
    ix, iy = lonlat_to_xy([initial_pose["lon"], initial_pose["lat"]], origin)
    ex, ey = lonlat_to_xy([estimated_pose["lon"], estimated_pose["lat"]], origin)
    return [round(ex - ix, 1), round(ey - iy, 1), round(estimated_pose["altitude_m"] - initial_pose["altitude_m"], 1)]


def _confidence(matched_points: int, inlier_ratio: float) -> float:
    return round(max(0.0, min(0.95, 0.22 + min(matched_points / 80, 1) * 0.28 + inlier_ratio * 0.5)), 3)


def _error_radius(confidence: float, inlier_ratio: float, matched_points: int) -> float:
    match_penalty = max(0.0, 35.0 - min(matched_points, 70) * 0.5)
    return round(max(8.0, 90.0 * (1 - confidence) + 30.0 * (1 - inlier_ratio) + match_penalty), 1)


def _safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def _navigation_effect(status: str) -> str:
    if status == "localized":
        return "opencv_orb visual observation can correct the simulated navigation state toward the estimated pose"
    if status == "needs_review":
        return "opencv_orb produced evidence but confidence is below autonomous navigation threshold"
    return "opencv_orb did not produce a navigation-grade visual observation"


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


@lru_cache(maxsize=1)
def _opencv_status() -> dict:
    if not find_spec("cv2"):
        return {
            "available": False,
            "version": "",
            "has_orb": False,
            "has_sift": False,
        }
    import cv2  # type: ignore

    return {
        "available": True,
        "version": getattr(cv2, "__version__", ""),
        "has_orb": hasattr(cv2, "ORB_create"),
        "has_sift": hasattr(cv2, "SIFT_create"),
    }
