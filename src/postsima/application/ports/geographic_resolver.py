from dataclasses import dataclass
from typing import Protocol

from postsima.domain.value_objects.coordinates import Coordinates


@dataclass(frozen=True, slots=True)
class GeographicData:
    municipality: str | None
    state: str | None


class GeographicResolver(Protocol):
    def resolve(self, coordinates: Coordinates) -> GeographicData | None:
        ...
