from fastapi import APIRouter, HTTPException

from app.api.responses import ok
from app.models.schemas import ApiResponse, RiskAnalysis, RiskZone, RiskZonesUpdateData, RiskZonesUpdateRequest, RiskAnalyzeRequest
from app.services.data_store import get_demo_data, get_risk_zones, get_task, replace_risk_zones
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


@router.get("/tasks/{task_id}/risk-zones", response_model=ApiResponse[list[RiskZone]])
def list_risk_zones(task_id: str):
    try:
        return ok(get_risk_zones(task_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/tasks/{task_id}/risk-zones", response_model=ApiResponse[RiskZonesUpdateData])
def update_risk_zones(task_id: str, payload: RiskZonesUpdateRequest):
    risk_zones = [zone.model_dump() for zone in payload.risk_zones]
    _validate_risk_zones(risk_zones)
    try:
        saved = replace_risk_zones(task_id, risk_zones)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"task_id": task_id, "risk_zones": saved, "count": len(saved)})


def _validate_risk_zones(risk_zones: list[dict]) -> None:
    ids = [zone["id"] for zone in risk_zones]
    duplicates = sorted({zone_id for zone_id in ids if ids.count(zone_id) > 1})
    if duplicates:
        raise HTTPException(status_code=422, detail=f"duplicate risk zone id: {', '.join(duplicates)}")

    for zone in risk_zones:
        polygon = zone["polygon"]
        if len(polygon) < 4:
            raise HTTPException(status_code=422, detail=f"risk zone {zone['id']} polygon requires at least 4 points")
        if polygon[0] != polygon[-1]:
            raise HTTPException(status_code=422, detail=f"risk zone {zone['id']} polygon must be closed")
