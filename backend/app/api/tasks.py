from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, LayerConfig, TaskDetailData, TaskEndpointsUpdateData, TaskEndpointsUpdateRequest, TaskSummary
from app.services.data_store import get_demo_data, get_task, update_task_endpoints

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=ApiResponse[list[TaskSummary]])
def list_tasks():
    data = get_demo_data()
    task = data["task"]
    return ok(
        [
            {
                "id": task["id"],
                "name": task["name"],
                "display_name": task["display_name"],
                "start": task["start"],
                "target": task["target"],
            }
        ]
    )


@router.get("/tasks/{task_id}", response_model=ApiResponse[TaskDetailData])
def task_detail(task_id: str):
    try:
        data = get_demo_data()
        task = get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"task": task, "risk_zones": data["risk_zones"], "obstacles": data["obstacles"]})


@router.put("/tasks/{task_id}/endpoints", response_model=ApiResponse[TaskEndpointsUpdateData])
def update_endpoints(task_id: str, payload: TaskEndpointsUpdateRequest):
    _validate_endpoint("start", payload.start)
    _validate_endpoint("target", payload.target)
    try:
        task = update_task_endpoints(task_id, payload.start, payload.target)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"task_id": task_id, "task": task})


def _validate_endpoint(label: str, point: list[float]) -> None:
    if len(point) != 3:
        raise HTTPException(status_code=422, detail=f"{label} requires [lon, lat, altitude]")
    lon, lat, altitude = point
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise HTTPException(status_code=422, detail=f"{label} longitude/latitude is out of range")
    if altitude < 0:
        raise HTTPException(status_code=422, detail=f"{label} altitude must be non-negative")


@router.get("/layers", response_model=ApiResponse[list[LayerConfig]])
def layers():
    return ok(get_demo_data()["layers"])
