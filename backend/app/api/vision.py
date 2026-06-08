from fastapi import APIRouter, HTTPException, Query

from app.api.responses import ok
from app.models.schemas import ApiResponse, VisionImage, VisionMatchRequest, VisionMatchResult, VisionTile
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
