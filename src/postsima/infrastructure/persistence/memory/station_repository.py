from uuid import UUID

from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station

class InMemoryStationRepository:
    def __init__(self) -> None:
        self._stations: dict[UUID, Station] = {}
        self._source_index: dict[tuple[int, str], UUID] = {}

    def get(self, station_id: UUID) -> Station | None:
        return  self._stations.get(station_id)

    def find_by_source_record(self, record: SourceRecord) -> Station | None:
        station_id = self._source_index.get(
            (record.source.value, record.external_id)
        )

        if station_id is None:
            return None

        return self._stations.get(station_id)

    def save(self, station: Station) -> None:
        self._stations[station.station_id] = station

        for record in station.source_records:
            self._source_index[(record.source.value, record.external_id)] = (
                station.station_id)

    def all(self) -> list[Station]:
        return list(self._stations.values())
