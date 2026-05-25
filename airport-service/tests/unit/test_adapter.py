"""
Unit tests for ApiColombiaAdapter.
All HTTP calls are mocked — no real network calls.
"""
import pytest
from unittest.mock import MagicMock, patch
import httpx

from app.infrastructure.adapters.api_colombia_adapter import ApiColombiaAdapter
from app.domain.entities.airport import Airport


MOCK_AIRPORTS = [
    {
        "id": 1,
        "name": "Aeropuerto Internacional El Dorado",
        "iataCode": "BOG",
        "oaciCode": "SKBO",
        "cityId": 1,
        "city": {"name": "Bogotá", "latitude": 4.7109886, "longitude": -74.072092},
    },
    {
        "id": 2,
        "name": "Aeropuerto Internacional José María Córdova",
        "iataCode": "MDE",
        "oaciCode": "SKRG",
        "cityId": 2,
        "city": {"name": "Medellín", "latitude": 6.167, "longitude": -75.433},
    },
]


@pytest.fixture
def mock_http_client():
    return MagicMock(spec=httpx.Client)


@pytest.fixture
def adapter(mock_http_client):
    return ApiColombiaAdapter(
        http_client=mock_http_client,
        base_url="https://fake-api.com/api/v1",
        timeout=5.0,
    )


class TestGetAllAirports:
    def test_returns_list_of_airport_entities(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_AIRPORTS
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_all_airports()

        assert len(result) == 2
        assert all(isinstance(a, Airport) for a in result)

    def test_maps_id_correctly(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [MOCK_AIRPORTS[0]]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_all_airports()
        assert result[0].id == "1"

    def test_maps_iata_code(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [MOCK_AIRPORTS[0]]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_all_airports()
        assert result[0].iata_code == "BOG"

    def test_maps_city_from_nested_object(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [MOCK_AIRPORTS[0]]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_all_airports()
        assert result[0].city == "Bogotá"

    def test_maps_coordinates(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [MOCK_AIRPORTS[0]]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_all_airports()
        assert result[0].latitude == 4.7109886
        assert result[0].longitude == -74.072092

    def test_raises_connection_error_on_timeout(self, adapter, mock_http_client):
        mock_http_client.get.side_effect = httpx.TimeoutException("timeout")
        with pytest.raises(ConnectionError, match="timed out"):
            adapter.get_all_airports()

    def test_skips_malformed_records(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            MOCK_AIRPORTS[0],
            None,  # malformed
        ]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        # Should not raise, just skip bad records
        result = adapter.get_all_airports()
        assert len(result) == 1


class TestGetAirportById:
    def test_returns_airport_when_found(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_AIRPORTS[0]
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = adapter.get_airport_by_id("1")
        assert result is not None
        assert result.id == "1"
        assert result.name == "Aeropuerto Internacional El Dorado"

    def test_returns_none_on_404(self, adapter, mock_http_client):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_http_client.get.return_value = mock_response

        result = adapter.get_airport_by_id("9999")
        assert result is None

    def test_raises_connection_error_on_network_failure(self, adapter, mock_http_client):
        mock_http_client.get.side_effect = httpx.RequestError("connection refused")
        with pytest.raises(ConnectionError):
            adapter.get_airport_by_id("1")
