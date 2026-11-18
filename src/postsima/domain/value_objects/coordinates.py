from dataclasses import dataclass
import math

@dataclass(frozen=True, slots=True)
class Coordinates:
    longitude: float
    latitude: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.longitude) or not math.isfinite(self.latitude):
            raise ValueError("Longitude and Latitude must be finite")

        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")

        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
