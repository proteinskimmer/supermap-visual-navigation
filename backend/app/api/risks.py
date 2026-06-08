from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, RiskAnalysis, RiskAnalyzeRequest
from app.services.data_store import get_demo_data, get_task
from app.services.risk_service import analyze_route

router = APIRouter(tags=["risks"])


@router.post("/risks/analyze", response_model=ApiResponse[RiskAnalysis])
def risks_analyze(payload: RiskAnalyzeRequest):
    data = get_demo_data()
    try:
        task = get_task(payload.task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok(analyze_route(task, payload.route.model_dump(), data["risk_zones"], data["obstacles"]))
