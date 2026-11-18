from collections import defaultdict
from math import floor
from uuid import UUID

from postsima.application.services.normalization import normalize_text
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station


class CandidateGenerator:
    def __init__(
        self,
        stations: list[Station],
        coordinate_cell_size: float = 0.01,
    ) -> None:
        self._stations = stations
        self._cell_size = coordinate_cell_size

        self._coordinates: dict[tuple[int, int], set[UUID]] = defaultdict(set)
        self._names: dict[str, set[UUID]] = defaultdict(set)
        self._postal_codes: dict[str, set[UUID]] = defaultdict(set)

        self._build_indexes()

    def find(self, record: SourceRecord) -> list[Station]:
        candidate_ids: set[UUID] = set()

        if record.coordinates:
            cell = self._coordinate_cell(record.coordinates.latitude, record.coordinates.longitude)

            for lat_offset in (-1, 0, 1):
                for lon_offset in (-1, 0, 1):
                    candidate_ids.update(
                        self._coordinates.get(
                            (cell[0] + lat_offset, cell[1] + lon_offset),
                            set(),
                        )
                    )

        name = normalize_text(record.name)
        if name:
            candidate_ids.update(self._names.get(name, set()))

        if record.postal_code:
            candidate_ids.update(
                self._postal_codes.get(
                    record.postal_code.value,
                    set(),
                )
            )

        stations_by_id = {
            station.station_id: station
            for station in self._stations
        }

        return [
            stations_by_id[station_id]
            for station_id in candidate_ids
            if station_id in stations_by_id and not any(
                source_record.source == record.source
                for source_record in stations_by_id[station_id].source_records
            )
        ]

    def _build_indexes(self) -> None:
        for station in self._stations:
            if station.coordinates:
                self._coordinates[
                    self._coordinate_cell(
                        station.coordinates.latitude,
                        station.coordinates.longitude,
                    )
                ].add(station.station_id)

            name = normalize_text(station.name)
            if name:
                self._names[name].add(station.station_id)

            if station.postal_code:
                self._postal_codes[
                    station.postal_code.value
                ].add(station.station_id)

    def _coordinate_cell(
        self,
        latitude: float,
        longitude: float,
    ) -> tuple[int, int]:
        return (
            floor(latitude / self._cell_size),
            floor(longitude / self._cell_size),
        )