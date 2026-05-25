"""Unit tests for ItineraryCommandService."""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from app.application.services.itinerary_command_service import ItineraryCommandService
from app.domain.entities.itinerary import Itinerary
from app.domain.ports.itinerary_repository_port import IItineraryRepository
from app.domain.ports.airport_validation_port import IAirportValidationPort

FUTURE = date.today() + timedelta(days=5)


@pytest.fixture
def mock_repo():
    return MagicMock(spec=IItineraryRepository)

@pytest.fixture
def mock_airport_port():
    return MagicMock(spec=IAirportValidationPort)

@pytest.fixture
def svc(mock_repo, mock_airport_port):
    return ItineraryCommandService(repo=mock_repo, airport_port=mock_airport_port)

@pytest.fixture
def existing(mock_repo):
    it = Itinerary("Ana", "1", "2", FUTURE, 90, id=1)
    mock_repo.find_by_id.return_value = it
    return it


class TestCreate:
    def test_validates_both_airports(self, svc, mock_airport_port, mock_repo):
        mock_airport_port.airport_exists.return_value = True
        mock_repo.save.return_value = Itinerary("Ana","1","2",FUTURE,90,id=1)
        svc.create("Ana","1","2",FUTURE,90)
        assert mock_airport_port.airport_exists.call_count == 2

    def test_raises_lookup_if_departure_missing(self, svc, mock_airport_port):
        mock_airport_port.airport_exists.return_value = False
        with pytest.raises(LookupError, match="Departure"):
            svc.create("Ana","BAD","2",FUTURE,90)

    def test_raises_lookup_if_arrival_missing(self, svc, mock_airport_port):
        mock_airport_port.airport_exists.side_effect = [True, False]
        with pytest.raises(LookupError, match="Arrival"):
            svc.create("Ana","1","BAD",FUTURE,90)

    def test_saves_after_validation(self, svc, mock_airport_port, mock_repo):
        mock_airport_port.airport_exists.return_value = True
        saved = Itinerary("Ana","1","2",FUTURE,90,id=1)
        mock_repo.save.return_value = saved
        result = svc.create("Ana","1","2",FUTURE,90)
        mock_repo.save.assert_called_once()
        assert result.id == 1


class TestUpdate:
    def test_returns_none_if_not_found(self, svc, mock_repo):
        mock_repo.find_by_id.return_value = None
        result = svc.update(999, user_name="Carlos")
        assert result is None

    def test_revalidates_airports_on_update(self, svc, mock_airport_port, mock_repo, existing):
        mock_airport_port.airport_exists.return_value = True
        mock_repo.update.return_value = existing
        svc.update(1, departure_airport_id="3")
        assert mock_airport_port.airport_exists.called


class TestDelete:
    def test_delegates_to_repo(self, svc, mock_repo):
        mock_repo.delete.return_value = True
        assert svc.delete(1) is True
        mock_repo.delete.assert_called_once_with(1)

    def test_returns_false_when_not_found(self, svc, mock_repo):
        mock_repo.delete.return_value = False
        assert svc.delete(999) is False
