"""Unit tests for ItineraryQueryService."""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from app.application.services.itinerary_query_service import ItineraryQueryService
from app.domain.entities.itinerary import Itinerary
from app.domain.ports.itinerary_repository_port import IItineraryRepository

FUTURE = date.today() + timedelta(days=5)

@pytest.fixture
def mock_repo(): return MagicMock(spec=IItineraryRepository)

@pytest.fixture
def svc(mock_repo): return ItineraryQueryService(repo=mock_repo)

@pytest.fixture
def sample():
    return [
        Itinerary("Ana","1","2",FUTURE,90,id=1),
        Itinerary("Carlos","2","3",FUTURE,120,id=2),
    ]

def test_get_all_returns_all(svc, mock_repo, sample):
    mock_repo.find_all.return_value = sample
    result = svc.get_all()
    assert len(result) == 2

def test_get_all_filters_by_user(svc, mock_repo, sample):
    mock_repo.find_all.return_value = [sample[0]]
    result = svc.get_all(user_name="Ana")
    mock_repo.find_all.assert_called_once_with(user_name="Ana")

def test_get_by_id_found(svc, mock_repo, sample):
    mock_repo.find_by_id.return_value = sample[0]
    result = svc.get_by_id(1)
    assert result.id == 1

def test_get_by_id_not_found(svc, mock_repo):
    mock_repo.find_by_id.return_value = None
    assert svc.get_by_id(999) is None
