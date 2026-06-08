from fastapi import APIRouter

from app.api.responses import ok
from app.models.schemas import ApiResponse, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthData])
def health():
    return ok({"status": "ok"})
