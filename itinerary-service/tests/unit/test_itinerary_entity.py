"""Unit tests for Itinerary domain entity."""
import pytest
from datetime import date, timedelta
from app.domain.entities.itinerary import Itinerary

FUTURE = date.today() + timedelta(days=10)


def test_valid_itinerary_creates_successfully():
    it = Itinerary("Ana", "1", "2", FUTURE, 90)
    assert it.user_name == "Ana"
    assert it.duration_minutes == 90


def test_raises_if_duration_zero():
    with pytest.raises(ValueError, match="duration_minutes"):
        Itinerary("Ana", "1", "2", FUTURE, 0)


def test_raises_if_duration_negative():
    with pytest.raises(ValueError):
        Itinerary("Ana", "1", "2", FUTURE, -10)


def test_raises_if_same_airports():
    with pytest.raises(ValueError, match="different"):
        Itinerary("Ana", "1", "1", FUTURE, 90)


def test_raises_if_empty_username():
    with pytest.raises(ValueError):
        Itinerary("", "1", "2", FUTURE, 90)


def test_apply_updates_returns_new_instance():
    original = Itinerary("Ana", "1", "2", FUTURE, 90, id=1)
    updated = original.apply_updates(user_name="Carlos", duration_minutes=120)
    assert updated.user_name == "Carlos"
    assert updated.duration_minutes == 120
    assert updated.departure_airport_id == "1"  # unchanged
    assert original.user_name == "Ana"  # original untouched
