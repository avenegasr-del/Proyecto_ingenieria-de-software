from pydantic import BaseModel, Field


class AirportResponse(BaseModel):
    id: str = Field(..., description="Unique airport identifier")
    name: str = Field(..., description="Airport name")
    city: str = Field(..., description="City where the airport is located")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    iata_code: str = Field(..., description="IATA code (e.g. BOG, MDE)")


class PlotlyAirportResponse(BaseModel):
    nombre: str = Field(..., description="Airport name")
    ciudad: str = Field(..., description="City name")
    latitud: float = Field(..., description="Latitude")
    longitud: float = Field(..., description="Longitude")
    codigo: str = Field(..., description="IATA code")


class HealthResponse(BaseModel):
    status: str
    service: str
    upstream: str
