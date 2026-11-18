from dataclasses import dataclass, field
from uuid import UUID

from postsima.domain.entities.charger import Charger
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode

@dataclass(slots=True)
class Station:
    station_id: UUID
    name: str | None = None
    address: str | None = None
    postal_code: PostalCode | None = None
    telephone: str | None = None
    coordinates: Coordinates | None = None
    municipality: str | None = None
    state: str | None = None
    price: str | None = None
    source_records: list[SourceRecord] = field(default_factory=list)
    chargers: list[Charger] = field(default_factory=list)

    def add_source_record(self, record: SourceRecord) -> None:
        if any(
                existing.identity == record.identity
                for existing in self.source_records
        ):
            raise ValueError(f"Source record {record.source.name}:"
                             f"{record.external_id} already exists")

        self.source_records.append(record)
