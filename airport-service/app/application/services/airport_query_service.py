import logging
from typing import List, Optional

from app.domain.entities.airport import Airport
from app.domain.ports.airport_external_port import IAirportExternalPort

logger = logging.getLogger(__name__)


class AirportQueryService:
    """
    Application service for airport queries.
    Orchestrates use cases using the abstract port.
    Has zero knowledge of ApiColombiaAdapter or httpx.

    Layer: Application
    """

    def __init__(self, airport_port: IAirportExternalPort):
        self._port = airport_port

    def list_all(self) -> List[Airport]:
        """Use case: list all available airports."""
        logger.info("Use case: list_all airports")
        return self._port.get_all_airports()

    def get_by_id(self, airport_id: str) -> Optional[Airport]:
        """Use case: get a single airport by ID."""
        logger.info(f"Use case: get_by_id airport_id={airport_id}")
        return self._port.get_airport_by_id(airport_id)

    def get_plotly_data(self) -> List[dict]:
        """Use case: transform airports into Plotly-ready format."""
        airports = self._port.get_all_airports()
        return [a.to_plotly_dict() for a in airports]

    def airport_exists(self, airport_id: str) -> bool:
        """Use case: check if an airport exists (used by Itinerary Service via HTTP)."""
        return self._port.get_airport_by_id(airport_id) is not None
