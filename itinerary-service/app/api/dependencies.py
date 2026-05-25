import httpx
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.config import settings
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_itinerary_repository import SqlAlchemyItineraryRepository
from app.infrastructure.adapters.airport_http_adapter import AirportServiceHttpAdapter
from app.application.services.itinerary_command_service import ItineraryCommandService
from app.application.services.itinerary_query_service import ItineraryQueryService


def get_repository(db: Session = Depends(get_db)) -> SqlAlchemyItineraryRepository:
    return SqlAlchemyItineraryRepository(db=db)


def get_airport_adapter() -> AirportServiceHttpAdapter:
    client = httpx.Client(timeout=settings.HTTP_TIMEOUT)
    return AirportServiceHttpAdapter(
        http_client=client,
        base_url=settings.AIRPORT_SERVICE_URL,
        timeout=settings.HTTP_TIMEOUT,
    )


def get_command_service(
    repo: SqlAlchemyItineraryRepository = Depends(get_repository),
    airport_adapter: AirportServiceHttpAdapter = Depends(get_airport_adapter),
) -> ItineraryCommandService:
    return ItineraryCommandService(repo=repo, airport_port=airport_adapter)


def get_query_service(
    repo: SqlAlchemyItineraryRepository = Depends(get_repository),
) -> ItineraryQueryService:
    return ItineraryQueryService(repo=repo)
