from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.responses import ok
from app.models.schemas import (
    ApiResponse,
    SyntheticViewRequest,
    SyntheticViewResponse,
    VisionImage,
    VisionMatchRequest,
    VisionMatchResult,
    VisionTile,
    VisualLocalizationRequest,
    VisualLocalizationResult,
)
from app.services.synthetic_view_service import (
    build_synthetic_view_response,
    get_localization,
    localize_with_synthetic_views,
)
from app.services.vision_matcher_provider import V05_EVIDENCE_DIR, matcher_runtime_status
from app.services.vision_service import (
    get_match_by_id,
    get_match_result,
    list_query_images,
    list_tile_index,
)

router = APIRouter(tags=["vision"])


@router.get("/vision/images", response_model=ApiResponse[list[VisionImage]])
def vision_images(task_id: str = Query(default="task_001")):
    return ok(list_query_images(task_id))


@router.get("/vision/tiles", response_model=ApiResponse[list[VisionTile]])
def vision_tiles(task_id: str = Query(default="task_001")):
    return ok(list_tile_index(task_id))


@router.get("/vision/matchers")
def vision_matchers():
    return ok(matcher_runtime_status())


@router.get("/vision/evidence/{filename}")
def vision_evidence_file(filename: str):
    safe_name = Path(filename).name
    path = (V05_EVIDENCE_DIR / safe_name).resolve()
    evidence_root = V05_EVIDENCE_DIR.resolve()
    if evidence_root not in path.parents or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"vision evidence not found: {filename}")
    return FileResponse(path)


@router.post("/vision/match", response_model=ApiResponse[VisionMatchResult])
def vision_match(payload: VisionMatchRequest):
    if payload.algorithm_mode != "precomputed":
        raise HTTPException(
            status_code=400,
            detail="only precomputed vision matching is available in the current demo",
        )
    result = get_match_result(payload.task_id, payload.image_id, payload.top_k)
    if result:
        return ok(result)
    raise HTTPException(status_code=404, detail=f"vision demo not found: {payload.image_id}")


@router.get("/vision/matches/{match_id}", response_model=ApiResponse[VisionMatchResult])
def vision_match_detail(match_id: str):
    result = get_match_by_id(match_id)
    if result:
        return ok(result)
    raise HTTPException(status_code=404, detail=f"vision match not found: {match_id}")


@router.post("/vision/synthetic-views", response_model=ApiResponse[SyntheticViewResponse])
def vision_synthetic_views(payload: SyntheticViewRequest):
    return ok(
        build_synthetic_view_response(
            task_id=payload.task_id,
            image_id=payload.image_id,
            initial_pose=payload.initial_pose.model_dump() if payload.initial_pose else None,
            route_prior_pose=payload.route_prior_pose.model_dump() if payload.route_prior_pose else None,
            top_k_tiles=payload.top_k_tiles,
            lighting_options=payload.lighting_options,
        )
    )


@router.post("/vision/localize", response_model=ApiResponse[VisualLocalizationResult])
def vision_localize(payload: VisualLocalizationRequest):
    return ok(
        localize_with_synthetic_views(
            task_id=payload.task_id,
            image_id=payload.image_id,
            initial_pose=payload.initial_pose.model_dump() if payload.initial_pose else None,
            route_prior_pose=payload.route_prior_pose.model_dump() if payload.route_prior_pose else None,
            top_k_tiles=payload.top_k_tiles,
            matcher_mode=payload.matcher_mode,
            lighting_options=payload.lighting_options,
        )
    )


@router.get("/vision/localizations/{image_id}", response_model=ApiResponse[VisualLocalizationResult])
def vision_localization_detail(image_id: str, task_id: str = Query(default="task_001")):
    return ok(get_localization(task_id, image_id))
