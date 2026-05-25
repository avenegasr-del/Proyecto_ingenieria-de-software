from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Itinerary:
    """Pure domain entity for a travel itinerary."""
    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.user_name or not self.user_name.strip():
            raise ValueError("user_name cannot be empty")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")
        if self.departure_airport_id == self.arrival_airport_id:
            raise ValueError("departure and arrival airports must be different")

    def apply_updates(self, **kwargs) -> "Itinerary":
        """Returns a new Itinerary with updated fields (immutable update)."""
        data = {
            "user_name": self.user_name,
            "departure_airport_id": self.departure_airport_id,
            "arrival_airport_id": self.arrival_airport_id,
            "travel_date": self.travel_date,
            "duration_minutes": self.duration_minutes,
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        data.update({k: v for k, v in kwargs.items() if v is not None})
        return Itinerary(**data)
