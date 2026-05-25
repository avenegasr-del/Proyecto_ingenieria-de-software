from abc import ABC, abstractmethod


class IAirportValidationPort(ABC):
    """Output port for validating airport existence via external service."""

    @abstractmethod
    def airport_exists(self, airport_id: str) -> bool: ...
