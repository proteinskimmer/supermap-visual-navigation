from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, LayerConfig, TaskDetailData, TaskSummary
from app.services.data_store import get_demo_data, get_task

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


@router.get("/layers", response_model=ApiResponse[list[LayerConfig]])
def layers():
    return ok(get_demo_data()["layers"])
