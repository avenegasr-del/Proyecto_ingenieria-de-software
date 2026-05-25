import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.api.schemas import HealthResponse
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check():
    # Check DB
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {e}"

    # Check Airport Service
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{settings.AIRPORT_SERVICE_URL}/health")
            airport_status = "healthy" if r.status_code == 200 else f"degraded ({r.status_code})"
    except Exception as e:
        airport_status = f"unreachable: {e}"

    return HealthResponse(
        status="ok",
        service="itinerary-service",
        database=db_status,
        airport_service=airport_status,
    )
