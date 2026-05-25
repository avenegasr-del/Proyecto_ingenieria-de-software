from sqlalchemy import Column, Integer, String, Date, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ItineraryModel(Base):
    __tablename__ = "itineraries"

    id                   = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_name            = Column(String(100), nullable=False, index=True)
    departure_airport_id = Column(String(20), nullable=False)
    arrival_airport_id   = Column(String(20), nullable=False)
    travel_date          = Column(Date, nullable=False)
    duration_minutes     = Column(Integer, nullable=False)
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at           = Column(DateTime(timezone=True), server_default=func.now(),
                                  onupdate=func.now(), nullable=False)
