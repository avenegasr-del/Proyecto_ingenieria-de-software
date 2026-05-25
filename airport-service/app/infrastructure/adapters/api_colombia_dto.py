from pydantic import BaseModel, Field
from typing import Optional


class ExternalAirportDTO(BaseModel):
    """
    Maps raw JSON from API Colombia.
    Isolates external field names from the internal domain model.
    """
    id: Optional[int] = None
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = None
    iataCode: Optional[str] = None
    oaciCode: Optional[str] = None
    cityId: Optional[int] = None
    city: Optional[dict] = None

    model_config = {"populate_by_name": True}

    def get_name(self) -> str:
        return self.name or "Unknown Airport"

    def get_city_name(self) -> str:
        if self.city and isinstance(self.city, dict):
            return self.city.get("name", "Unknown City")
        return "Unknown City"

    def get_latitude(self) -> float:
        if self.city and isinstance(self.city, dict):
            try:
                return float(self.city.get("latitude", 0.0) or 0.0)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    def get_longitude(self) -> float:
        if self.city and isinstance(self.city, dict):
            try:
                return float(self.city.get("longitude", 0.0) or 0.0)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    def get_iata_code(self) -> str:
        return self.iataCode or ""
