import httpx
from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Check service health and upstream API Colombia connectivity."""
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{settings.API_COLOMBIA_URL}/Airport?page=1&perPage=1")
            upstream = "healthy" if r.status_code == 200 else f"degraded ({r.status_code})"
    except Exception as e:
        upstream = f"unreachable ({e})"
    return HealthResponse(
        status="ok",
        service="airport-service",
        upstream=upstream,
    )
