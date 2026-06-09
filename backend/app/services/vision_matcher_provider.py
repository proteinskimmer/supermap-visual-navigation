from __future__ import annotations

from functools import lru_cache
from importlib.util import find_spec


PRECOMPUTED_MATCHER_MODES = {"synthetic_v04", "precomputed", "precomputed_proxy"}
REAL_MATCHER_MODES = {"opencv_orb", "opencv_sift", "external_deep_matcher"}
SUPPORTED_MATCHER_MODES = PRECOMPUTED_MATCHER_MODES | REAL_MATCHER_MODES


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
            "status": "planned" if cv2["available"] else "unavailable",
            "provider": "opencv_orb",
            "cv2_available": cv2["available"],
            "cv2_version": cv2["version"],
            "algorithm_available": cv2["has_orb"],
            "description": "v0.5 target provider; implementation is planned after OpenCV is available.",
        },
        "opencv_sift": {
            "status": "planned" if cv2["available"] and cv2["has_sift"] else "unavailable",
            "provider": "opencv_sift",
            "cv2_available": cv2["available"],
            "cv2_version": cv2["version"],
            "algorithm_available": cv2["has_sift"],
            "description": "Optional v0.5 provider; depends on OpenCV SIFT support.",
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
        if normalized == "opencv_sift" and not cv2["has_sift"]:
            return "OpenCV is installed, but SIFT_create is not available."
        return f"{normalized} provider is reserved for v0.5 and has not been implemented yet."
    if normalized == "external_deep_matcher":
        return "External deep matcher provider is reserved for v0.5 integration."
    return f"Unsupported matcher mode: {mode}"


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
