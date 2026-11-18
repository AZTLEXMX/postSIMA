from typing import Protocol
from uuid import UUID

from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station

class StationRepository(Protocol):
    def get(self, station_id: UUID) -> Station | None:
        ...

    def find_by_source_record(self, record: SourceRecord) -> Station | None:
        ...

    def save(self, station: Station | None) -> None:
        ...

    def all(self) -> list[Station]:
        ...
