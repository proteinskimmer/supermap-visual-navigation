from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, ReportData
from app.services.data_store import get_demo_data, get_task
from app.services.planning_service import plan_routes
from app.services.risk_service import analyze_route, build_simulation_events
from app.services.vision_service import build_vision_event, build_vision_summary, get_match_result, list_query_images

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
    vision_images = list_query_images(task_id)
    first_image = vision_images[0] if vision_images else {"id": "demo_uav_001", "capture_time_s": 0}
    vision = get_match_result(task_id, first_image["id"]) or get_match_result(task_id, "demo_uav_001")
    if not vision:
        raise HTTPException(status_code=404, detail=f"vision report data not found for task: {task_id}")
    events = build_simulation_events(route)
    events.append(build_vision_event(vision, first_image.get("capture_time_s")))
    events = sorted(events, key=lambda event: event["time_s"])
    return ok(
        {
            "task": task,
            "recommended_route": route,
            "risk": risk,
            "events": events,
            "vision": vision,
            "vision_summary": build_vision_summary(task_id),
            "summary": "本报告基于示范数据生成，用于比赛演示和系统联调。",
        }
    )
