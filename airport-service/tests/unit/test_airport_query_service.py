"""
Unit tests for AirportQueryService.
Uses mock implementations of IAirportExternalPort — zero real I/O.
"""
import pytest
from unittest.mock import MagicMock

from app.application.services.airport_query_service import AirportQueryService
from app.domain.entities.airport import Airport
from app.domain.ports.airport_external_port import IAirportExternalPort


@pytest.fixture
def mock_port() -> IAirportExternalPort:
    return MagicMock(spec=IAirportExternalPort)


@pytest.fixture
def service(mock_port) -> AirportQueryService:
    return AirportQueryService(airport_port=mock_port)


@pytest.fixture
def sample_airports():
    return [
        Airport("1", "El Dorado", "Bogotá", 4.71, -74.07, "BOG"),
        Airport("2", "José María Córdova", "Medellín", 6.17, -75.43, "MDE"),
    ]


class TestListAll:
    def test_delegates_to_port(self, service, mock_port, sample_airports):
        mock_port.get_all_airports.return_value = sample_airports
        result = service.list_all()
        mock_port.get_all_airports.assert_called_once()
        assert result == sample_airports

    def test_returns_empty_list_when_no_airports(self, service, mock_port):
        mock_port.get_all_airports.return_value = []
        result = service.list_all()
        assert result == []


class TestGetById:
    def test_returns_airport_when_exists(self, service, mock_port, sample_airports):
        mock_port.get_airport_by_id.return_value = sample_airports[0]
        result = service.get_by_id("1")
        mock_port.get_airport_by_id.assert_called_once_with("1")
        assert result == sample_airports[0]

    def test_returns_none_when_not_found(self, service, mock_port):
        mock_port.get_airport_by_id.return_value = None
        result = service.get_by_id("INVALID")
        assert result is None


class TestGetPlotlyData:
    def test_returns_list_of_dicts(self, service, mock_port, sample_airports):
        mock_port.get_all_airports.return_value = sample_airports
        result = service.get_plotly_data()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_plotly_dict_has_required_keys(self, service, mock_port, sample_airports):
        mock_port.get_all_airports.return_value = [sample_airports[0]]
        result = service.get_plotly_data()
        keys = result[0].keys()
        assert "nombre" in keys
        assert "ciudad" in keys
        assert "latitud" in keys
        assert "longitud" in keys
        assert "codigo" in keys

    def test_plotly_values_correct(self, service, mock_port, sample_airports):
        mock_port.get_all_airports.return_value = [sample_airports[0]]
        result = service.get_plotly_data()
        assert result[0]["nombre"] == "El Dorado"
        assert result[0]["ciudad"] == "Bogotá"
        assert result[0]["latitud"] == 4.71
        assert result[0]["codigo"] == "BOG"


class TestAirportExists:
    def test_returns_true_when_airport_found(self, service, mock_port, sample_airports):
        mock_port.get_airport_by_id.return_value = sample_airports[0]
        assert service.airport_exists("1") is True

    def test_returns_false_when_not_found(self, service, mock_port):
        mock_port.get_airport_by_id.return_value = None
        assert service.airport_exists("9999") is False
