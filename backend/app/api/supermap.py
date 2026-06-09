from fastapi import APIRouter

from app.api.responses import ok
from app.models.schemas import ApiResponse, SuperMapServiceSummary
from app.services.supermap_config_service import get_supermap_config, get_supermap_status, list_supermap_services

router = APIRouter(tags=["supermap"])


@router.get("/supermap/config", response_model=ApiResponse[dict])
def supermap_config():
    return ok(get_supermap_config())


@router.get("/supermap/services", response_model=ApiResponse[list[SuperMapServiceSummary]])
def supermap_services():
    return ok(list_supermap_services())


@router.get("/supermap/status", response_model=ApiResponse[dict])
def supermap_status():
    return ok(get_supermap_status())
