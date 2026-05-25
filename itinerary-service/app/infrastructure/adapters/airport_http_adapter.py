import logging
import httpx
from app.domain.ports.airport_validation_port import IAirportValidationPort
from app.core.config import settings

logger = logging.getLogger(__name__)


class AirportServiceHttpAdapter(IAirportValidationPort):
    """
    Adapter that validates airports by calling the Airport Service via HTTP.
    Implements IAirportValidationPort (output port).
    """

    def __init__(self, http_client: httpx.Client, base_url: str, timeout: float = 10.0):
        self._client = http_client
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def airport_exists(self, airport_id: str) -> bool:
        try:
            url = f"{self._base_url}/airports/{airport_id}"
            logger.info(f"Validating airport {airport_id} at {url}")
            response = self._client.get(url, timeout=self._timeout)
            return response.status_code == 200
        except httpx.TimeoutException:
            logger.error(f"Timeout validating airport {airport_id}")
            raise ConnectionError("Airport Service timed out")
        except httpx.RequestError as e:
            logger.error(f"Airport Service unreachable: {e}")
            raise ConnectionError(f"Airport Service unavailable: {e}")
