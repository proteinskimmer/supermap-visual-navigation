from fastapi import APIRouter, Query

from app.api.responses import ok
from app.models.schemas import (
    ApiResponse,
    NavigationLocalizeRequest,
    NavigationReplanRequest,
    NavigationSession,
    NavigationStartRequest,
    NavigationStateFrame,
    NavigationVisualFrame,
    ReplanData,
)
from app.services.visual_navigation_service import (
    get_navigation_state,
    get_navigation_timeline,
    localize_visual_frame,
    replan_from_navigation_state,
    start_navigation_session,
)

router = APIRouter(tags=["navigation"])


@router.post("/navigation/start", response_model=ApiResponse[NavigationSession])
def navigation_start(payload: NavigationStartRequest):
    return ok(start_navigation_session(payload.task_id, payload.route.model_dump(), payload.mode))


@router.get("/navigation/state", response_model=ApiResponse[NavigationStateFrame])
def navigation_state(session_id: str = Query(...), time_s: int = Query(default=0, ge=0)):
    return ok(get_navigation_state(session_id, time_s))


@router.get("/navigation/timeline", response_model=ApiResponse[NavigationSession])
def navigation_timeline(session_id: str = Query(...)):
    return ok(get_navigation_timeline(session_id))


@router.post("/navigation/localize", response_model=ApiResponse[NavigationVisualFrame])
def navigation_localize(payload: NavigationLocalizeRequest):
    return ok(localize_visual_frame(payload.task_id, payload.image_id))


@router.post("/navigation/replan", response_model=ApiResponse[ReplanData])
def navigation_replan(payload: NavigationReplanRequest):
    temporary_risks = [risk.model_dump() for risk in payload.temporary_risks]
    return ok(replan_from_navigation_state(payload.session_id, payload.time_s, temporary_risks))
