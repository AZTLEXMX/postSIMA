from dataclasses import dataclass, field

from postsima.domain.entities.charger import Charger
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode

@dataclass(slots=True)
class SourceRecord:
    source: Source
    external_id: str
    name: str | None = None
    address: str | None = None
    postal_code: PostalCode | None = None
    telephone: str | None = None
    coordinates: Coordinates | None = None
    price: str | None = None
    chargers: list[Charger] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.external_id.strip():
            raise ValueError("external_id can't be empty.")

    @property
    def identity(self) -> tuple[Source, str]:
        return self.source, self.external_id