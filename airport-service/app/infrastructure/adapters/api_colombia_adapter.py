import logging
from typing import List, Optional

import httpx

from app.domain.entities.airport import Airport
from app.domain.ports.airport_external_port import IAirportExternalPort
from app.infrastructure.adapters.api_colombia_dto import ExternalAirportDTO

logger = logging.getLogger(__name__)


class ApiColombiaAdapter(IAirportExternalPort):
    """
    Concrete Adapter implementing IAirportExternalPort.

    This class is the ONLY component in the system that knows:
    - The URL structure of API Colombia
    - The JSON field names of the external API
    - How to map external data to internal domain models

    Pattern: Adapter (Wrapper)
    Layer: Infrastructure
    """

    def __init__(self, http_client: httpx.Client, base_url: str, timeout: float = 10.0):
        self._client = http_client
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def get_all_airports(self) -> List[Airport]:
        """Fetches all airports from API Colombia and maps them to domain entities."""
        try:
            url = f"{self._base_url}/Airport"
            logger.info(f"Fetching airports from: {url}")
            response = self._client.get(url, timeout=self._timeout)
            response.raise_for_status()
            raw_data = response.json()
            airports = []
            for item in raw_data:
                try:
                    dto = ExternalAirportDTO(**item)
                    airport = self._map_to_domain(dto)
                    airports.append(airport)
                except Exception as e:
                    logger.warning(f"Skipping malformed airport record: {e}")
            logger.info(f"Successfully mapped {len(airports)} airports")
            return airports
        except httpx.TimeoutException:
            logger.error("Timeout while fetching airports from API Colombia")
            raise ConnectionError("API Colombia timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from API Colombia: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise ConnectionError(f"Could not reach API Colombia: {e}")

    def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        """Fetches a single airport by ID from API Colombia."""
        try:
            url = f"{self._base_url}/Airport/{airport_id}"
            logger.info(f"Fetching airport {airport_id} from: {url}")
            response = self._client.get(url, timeout=self._timeout)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            dto = ExternalAirportDTO(**response.json())
            return self._map_to_domain(dto)
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching airport {airport_id}")
            raise ConnectionError("API Colombia timed out")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for airport {airport_id}: {e}")
            raise ConnectionError(f"Could not reach API Colombia: {e}")

    @staticmethod
    def _map_to_domain(dto: ExternalAirportDTO) -> Airport:
        """
        Maps ExternalAirportDTO -> Airport (domain entity).
        This is the core translation of the Adapter pattern.
        """
        return Airport(
            id=str(dto.id or ""),
            name=dto.get_name(),
            city=dto.get_city_name(),
            latitude=dto.get_latitude(),
            longitude=dto.get_longitude(),
            iata_code=dto.get_iata_code(),
        )
