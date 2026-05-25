from dataclasses import dataclass


@dataclass(frozen=True)
class Airport:
    """Pure domain entity. No framework dependencies."""
    id: str
    name: str
    city: str
    latitude: float
    longitude: float
    iata_code: str

    def to_plotly_dict(self) -> dict:
        return {
            "nombre": self.name,
            "ciudad": self.city,
            "latitud": self.latitude,
            "longitud": self.longitude,
            "codigo": self.iata_code,
        }
