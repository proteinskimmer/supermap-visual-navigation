from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, ReportData
from app.services.data_store import get_demo_data, get_task
from app.services.planning_service import plan_routes
from app.services.risk_service import analyze_route, build_simulation_events
from app.services.vision_service import get_match_result

router = APIRouter(tags=["reports"])


@router.get("/reports/{task_id}", response_model=ApiResponse[ReportData])
def report(task_id: str):
    data = get_demo_data()
    try:
        task = get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    route = plan_routes(task, data["risk_zones"], ["balanced"])[0]
    risk = analyze_route(task, route, data["risk_zones"], data["obstacles"])
    vision = get_match_result(task_id, data["vision_images"][0]["id"]) or get_match_result(task_id, "demo_uav_001")
    if not vision:
        raise HTTPException(status_code=404, detail=f"vision report data not found for task: {task_id}")
    return ok(
        {
            "task": task,
            "recommended_route": route,
            "risk": risk,
            "events": build_simulation_events(route),
            "vision": vision,
            "summary": "本报告基于示范数据生成，用于比赛演示和系统联调。",
        }
    )
