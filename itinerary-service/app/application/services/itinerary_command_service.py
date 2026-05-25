import logging
from typing import Optional

from app.domain.entities.itinerary import Itinerary
from app.domain.ports.itinerary_repository_port import IItineraryRepository
from app.domain.ports.airport_validation_port import IAirportValidationPort

logger = logging.getLogger(__name__)


class ItineraryCommandService:
    """
    Application service: write operations (create, update, delete).
    Orchestrates domain logic + port calls.
    """

    def __init__(self, repo: IItineraryRepository, airport_port: IAirportValidationPort):
        self._repo = repo
        self._airport_port = airport_port

    def _validate_airports(self, departure_id: str, arrival_id: str) -> None:
        """Validates both airports exist via the airport validation port."""
        if not self._airport_port.airport_exists(departure_id):
            raise LookupError(f"Departure airport not found: '{departure_id}'")
        if not self._airport_port.airport_exists(arrival_id):
            raise LookupError(f"Arrival airport not found: '{arrival_id}'")

    def create(self, user_name: str, departure_airport_id: str, arrival_airport_id: str,
               travel_date, duration_minutes: int) -> Itinerary:
        logger.info(f"Creating itinerary for user={user_name}")
        self._validate_airports(departure_airport_id, arrival_airport_id)
        itinerary = Itinerary(
            user_name=user_name,
            departure_airport_id=departure_airport_id,
            arrival_airport_id=arrival_airport_id,
            travel_date=travel_date,
            duration_minutes=duration_minutes,
        )
        saved = self._repo.save(itinerary)
        logger.info(f"Itinerary created id={saved.id}")
        return saved

    def update(self, itinerary_id: int, **kwargs) -> Optional[Itinerary]:
        logger.info(f"Updating itinerary id={itinerary_id}")
        existing = self._repo.find_by_id(itinerary_id)
        if not existing:
            return None
        dep_id = kwargs.get("departure_airport_id") or existing.departure_airport_id
        arr_id = kwargs.get("arrival_airport_id") or existing.arrival_airport_id
        self._validate_airports(dep_id, arr_id)
        updated = existing.apply_updates(**kwargs)
        return self._repo.update(updated)

    def delete(self, itinerary_id: int) -> bool:
        logger.info(f"Deleting itinerary id={itinerary_id}")
        return self._repo.delete(itinerary_id)
