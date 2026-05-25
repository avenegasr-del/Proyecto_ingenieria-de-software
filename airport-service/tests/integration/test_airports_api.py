"""Integration tests using FastAPI TestClient."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.domain.entities.airport import Airport
from app.application.services.airport_query_service import AirportQueryService
from app.api.dependencies import get_airport_service

AIRPORTS = [
    Airport("1", "El Dorado", "Bogotá", 4.71, -74.07, "BOG"),
    Airport("2", "José María Córdova", "Medellín", 6.17, -75.43, "MDE"),
]

def override_service():
    svc = MagicMock(spec=AirportQueryService)
    svc.list_all.return_value = AIRPORTS
    svc.get_by_id.side_effect = lambda aid: next((a for a in AIRPORTS if a.id == aid), None)
    svc.get_plotly_data.return_value = [a.to_plotly_dict() for a in AIRPORTS]
    return svc

app.dependency_overrides[get_airport_service] = override_service
client = TestClient(app)

def test_list_airports_returns_200():
    r = client.get("/airports")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_list_airports_response_shape():
    r = client.get("/airports")
    item = r.json()[0]
    assert "id" in item
    assert "name" in item
    assert "city" in item
    assert "latitude" in item
    assert "longitude" in item
    assert "iata_code" in item

def test_get_airport_by_id_found():
    r = client.get("/airports/1")
    assert r.status_code == 200
    assert r.json()["iata_code"] == "BOG"

def test_get_airport_by_id_not_found():
    r = client.get("/airports/9999")
    assert r.status_code == 404

def test_plotly_endpoint_returns_correct_keys():
    r = client.get("/airports/plotly")
    assert r.status_code == 200
    item = r.json()[0]
    assert "nombre" in item
    assert "ciudad" in item
    assert "latitud" in item
    assert "longitud" in item
    assert "codigo" in item

def test_root_returns_service_info():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "airport-service"
