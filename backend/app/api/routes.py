from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, ReplanData, ReplanRequest, Route, RoutePlanRequest
from app.services.data_store import get_demo_data, get_task
from app.services.planning_service import plan_routes, replan_route

router = APIRouter(tags=["routes"])


@router.post("/routes/plan", response_model=ApiResponse[list[Route]])
def routes_plan(payload: RoutePlanRequest):
    data = get_demo_data()
    try:
        task = get_task(payload.task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if payload.start:
        task["start"] = payload.start
    if payload.target:
        task["target"] = payload.target
    return ok(plan_routes(task, data["risk_zones"], payload.modes))


@router.post("/routes/replan", response_model=ApiResponse[ReplanData])
def routes_replan(payload: ReplanRequest):
    data = get_demo_data()
    try:
        task = get_task(payload.task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    risk_zones = data["risk_zones"] + [risk.model_dump() for risk in payload.temporary_risks]
    route = replan_route(task, risk_zones, payload.current_position, payload.target or task["target"])
    return ok(
        {
            "route": route,
            "event": {
                "time_s": payload.time_s,
                "type": "replan",
                "title": "动态重规划完成",
                "description": "系统已绕开新增风险区并生成接续航线。",
                "position": payload.current_position,
            },
        }
    )
