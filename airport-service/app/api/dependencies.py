import httpx
from functools import lru_cache

from app.core.config import settings
from app.infrastructure.adapters.api_colombia_adapter import ApiColombiaAdapter
from app.application.services.airport_query_service import AirportQueryService


def get_http_client() -> httpx.Client:
    return httpx.Client(timeout=settings.HTTP_TIMEOUT)


def get_airport_service() -> AirportQueryService:
    """
    Dependency injection factory.
    Wires: AirportQueryService -> ApiColombiaAdapter -> httpx.Client
    """
    client = get_http_client()
    adapter = ApiColombiaAdapter(
        http_client=client,
        base_url=settings.API_COLOMBIA_URL,
        timeout=settings.HTTP_TIMEOUT,
    )
    return AirportQueryService(airport_port=adapter)
