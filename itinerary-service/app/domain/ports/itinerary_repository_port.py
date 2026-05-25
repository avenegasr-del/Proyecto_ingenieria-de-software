from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.itinerary import Itinerary


class IItineraryRepository(ABC):
    """Output port for itinerary persistence."""

    @abstractmethod
    def save(self, itinerary: Itinerary) -> Itinerary: ...

    @abstractmethod
    def find_by_id(self, itinerary_id: int) -> Optional[Itinerary]: ...

    @abstractmethod
    def find_all(self, user_name: Optional[str] = None) -> List[Itinerary]: ...

    @abstractmethod
    def update(self, itinerary: Itinerary) -> Itinerary: ...

    @abstractmethod
    def delete(self, itinerary_id: int) -> bool: ...
