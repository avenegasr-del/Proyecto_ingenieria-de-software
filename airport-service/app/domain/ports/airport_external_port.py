from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.airport import Airport


class IAirportExternalPort(ABC):
    """
    Output port (driven port).
    Abstracts any external source of airport data.
    The domain depends on this interface, not on any concrete implementation.
    """

    @abstractmethod
    def get_all_airports(self) -> List[Airport]:
        """Retrieve all available airports."""
        ...

    @abstractmethod
    def get_airport_by_id(self, airport_id: str) -> Optional[Airport]:
        """Retrieve a single airport by its unique ID. Returns None if not found."""
        ...
