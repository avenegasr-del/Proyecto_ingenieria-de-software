"""Integration tests using FastAPI TestClient with in-memory SQLite."""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.main import app
from app.api.dependencies import get_command_service, get_query_service, get_repository, get_airport_adapter
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_itinerary_repository import SqlAlchemyItineraryRepository
from app.infrastructure.adapters.airport_http_adapter import AirportServiceHttpAdapter
from app.application.services.itinerary_command_service import ItineraryCommandService
from app.application.services.itinerary_query_service import ItineraryQueryService

FUTURE = (date.today() + timedelta(days=7)).isoformat()

# In-memory test database using a shared SQLite pool so the schema stays available across sessions
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=TEST_ENGINE)

def override_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

def override_airport_adapter():
    mock = MagicMock(spec=AirportServiceHttpAdapter)
    mock.airport_exists.return_value = True
    return mock

def override_command_service():
    db = TestSession()
    repo = SqlAlchemyItineraryRepository(db=db)
    airport = override_airport_adapter()
    return ItineraryCommandService(repo=repo, airport_port=airport)

def override_query_service():
    db = TestSession()
    repo = SqlAlchemyItineraryRepository(db=db)
    return ItineraryQueryService(repo=repo)

Base.metadata.create_all(bind=TEST_ENGINE)
app.dependency_overrides[get_db] = override_db
app.dependency_overrides[get_airport_adapter] = override_airport_adapter
app.dependency_overrides[get_command_service] = override_command_service
app.dependency_overrides[get_query_service] = override_query_service

client = TestClient(app)

PAYLOAD = {
    "user_name": "Ana García",
    "departure_airport_id": "1",
    "arrival_airport_id": "2",
    "travel_date": FUTURE,
    "duration_minutes": 90,
}

def test_create_itinerary_returns_201():
    r = client.post("/itineraries", json=PAYLOAD)
    assert r.status_code == 201

def test_create_itinerary_response_shape():
    r = client.post("/itineraries", json=PAYLOAD)
    data = r.json()
    assert "id" in data
    assert "user_name" in data
    assert "departure_airport_id" in data
    assert "arrival_airport_id" in data
    assert "travel_date" in data
    assert "duration_minutes" in data

def test_list_itineraries_returns_200():
    r = client.get("/itineraries")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_get_itinerary_by_id():
    r = client.post("/itineraries", json=PAYLOAD)
    created_id = r.json()["id"]
    r2 = client.get(f"/itineraries/{created_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == created_id

def test_get_nonexistent_itinerary_returns_404():
    r = client.get("/itineraries/99999")
    assert r.status_code == 404

def test_update_itinerary():
    r = client.post("/itineraries", json=PAYLOAD)
    iid = r.json()["id"]
    r2 = client.put(f"/itineraries/{iid}", json={"user_name": "Carlos López", "duration_minutes": 120})
    assert r2.status_code == 200
    assert r2.json()["user_name"] == "Carlos López"
    assert r2.json()["duration_minutes"] == 120

def test_delete_itinerary():
    r = client.post("/itineraries", json=PAYLOAD)
    iid = r.json()["id"]
    r2 = client.delete(f"/itineraries/{iid}")
    assert r2.status_code == 204
    r3 = client.get(f"/itineraries/{iid}")
    assert r3.status_code == 404

def test_create_with_past_date_returns_422():
    bad = {**PAYLOAD, "travel_date": "2000-01-01"}
    r = client.post("/itineraries", json=bad)
    assert r.status_code == 422

def test_create_with_same_airports_returns_422():
    bad = {**PAYLOAD, "departure_airport_id": "1", "arrival_airport_id": "1"}
    r = client.post("/itineraries", json=bad)
    assert r.status_code == 422
