from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime
from typing import Optional


class ItineraryCreate(BaseModel):
    user_name: str            = Field(..., min_length=1, max_length=100, examples=["María García"])
    departure_airport_id: str = Field(..., min_length=1, examples=["1"])
    arrival_airport_id: str   = Field(..., min_length=1, examples=["2"])
    travel_date: date         = Field(..., examples=["2025-12-01"])
    duration_minutes: int     = Field(..., gt=0, examples=[90])

    @field_validator("travel_date")
    @classmethod
    def travel_date_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("travel_date cannot be in the past")
        return v

    @model_validator(mode="after")
    def airports_must_differ(self) -> "ItineraryCreate":
        if self.departure_airport_id == self.arrival_airport_id:
            raise ValueError("departure and arrival airports must be different")
        return self


class ItineraryUpdate(BaseModel):
    user_name: Optional[str]            = Field(None, min_length=1, max_length=100)
    departure_airport_id: Optional[str] = Field(None, min_length=1)
    arrival_airport_id: Optional[str]   = Field(None, min_length=1)
    travel_date: Optional[date]         = None
    duration_minutes: Optional[int]     = Field(None, gt=0)

    @field_validator("travel_date")
    @classmethod
    def travel_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("travel_date cannot be in the past")
        return v


class ItineraryResponse(BaseModel):
    id: int
    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    airport_service: str
