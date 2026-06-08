from fastapi import APIRouter

from app.api.responses import ok
from app.models.schemas import ApiResponse, SimulationStartData, SimulationStartRequest, TemporaryRiskData, TemporaryRiskRequest
from app.services.risk_service import build_simulation_events, temporary_risk_polygon

router = APIRouter(tags=["simulations"])


@router.post("/simulations/start", response_model=ApiResponse[SimulationStartData])
def simulations_start(payload: SimulationStartRequest):
    route = payload.route.model_dump()
    return ok(
        {
            "simulation_id": "sim_001",
            "route": route,
            "events": build_simulation_events(route),
            "state": "ready",
        }
    )


@router.post("/simulations/{simulation_id}/temporary-risk", response_model=ApiResponse[TemporaryRiskData])
def add_temporary_risk(simulation_id: str, payload: TemporaryRiskRequest):
    risk = {
        "id": "risk_temp_001",
        "name": "临时禁飞区",
        "type": "no_fly",
        "level": 5,
        "buffer_m": 120,
        "active": True,
        "polygon": temporary_risk_polygon(payload.current_position),
    }
    return ok(
        {
            "simulation_id": simulation_id,
            "risk": risk,
            "affected": True,
            "event": {
                "time_s": payload.time_s,
                "type": "risk_alert",
                "title": "检测到临时风险区",
                "description": "当前航线剩余段与临时禁飞区相交，触发局部重规划。",
                "position": payload.current_position,
            },
        }
    )
