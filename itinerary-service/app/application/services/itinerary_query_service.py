import logging
from typing import List, Optional

from app.domain.entities.itinerary import Itinerary
from app.domain.ports.itinerary_repository_port import IItineraryRepository

logger = logging.getLogger(__name__)


class ItineraryQueryService:
    """Application service: read operations."""

    def __init__(self, repo: IItineraryRepository):
        self._repo = repo

    def get_all(self, user_name: Optional[str] = None) -> List[Itinerary]:
        logger.info(f"Listing itineraries user_name={user_name}")
        return self._repo.find_all(user_name=user_name)

    def get_by_id(self, itinerary_id: int) -> Optional[Itinerary]:
        logger.info(f"Fetching itinerary id={itinerary_id}")
        return self._repo.find_by_id(itinerary_id)
