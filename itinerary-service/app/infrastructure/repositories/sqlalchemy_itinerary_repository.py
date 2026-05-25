from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.entities.itinerary import Itinerary
from app.domain.ports.itinerary_repository_port import IItineraryRepository
from app.infrastructure.database.models import ItineraryModel


class SqlAlchemyItineraryRepository(IItineraryRepository):
    """Concrete repository using SQLAlchemy. Implements IItineraryRepository."""

    def __init__(self, db: Session):
        self._db = db

    def save(self, itinerary: Itinerary) -> Itinerary:
        model = ItineraryModel(
            user_name=itinerary.user_name,
            departure_airport_id=itinerary.departure_airport_id,
            arrival_airport_id=itinerary.arrival_airport_id,
            travel_date=itinerary.travel_date,
            duration_minutes=itinerary.duration_minutes,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, itinerary_id: int) -> Optional[Itinerary]:
        model = self._db.query(ItineraryModel).filter(
            ItineraryModel.id == itinerary_id
        ).first()
        return self._to_entity(model) if model else None

    def find_all(self, user_name: Optional[str] = None) -> List[Itinerary]:
        query = self._db.query(ItineraryModel)
        if user_name:
            query = query.filter(ItineraryModel.user_name == user_name)
        return [self._to_entity(m) for m in query.order_by(ItineraryModel.id.desc()).all()]

    def update(self, itinerary: Itinerary) -> Itinerary:
        model = self._db.query(ItineraryModel).filter(
            ItineraryModel.id == itinerary.id
        ).first()
        if not model:
            raise ValueError(f"Itinerary {itinerary.id} not found")
        model.user_name            = itinerary.user_name
        model.departure_airport_id = itinerary.departure_airport_id
        model.arrival_airport_id   = itinerary.arrival_airport_id
        model.travel_date          = itinerary.travel_date
        model.duration_minutes     = itinerary.duration_minutes
        model.updated_at           = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def delete(self, itinerary_id: int) -> bool:
        model = self._db.query(ItineraryModel).filter(
            ItineraryModel.id == itinerary_id
        ).first()
        if not model:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    @staticmethod
    def _to_entity(model: ItineraryModel) -> Itinerary:
        return Itinerary(
            id=model.id,
            user_name=model.user_name,
            departure_airport_id=model.departure_airport_id,
            arrival_airport_id=model.arrival_airport_id,
            travel_date=model.travel_date,
            duration_minutes=model.duration_minutes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
