from uuid import uuid4

from postsima.application.models.consolidation import (
    ConflictValue,
    FieldConflict,
)
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station


class StationConsolidator:
    def consolidate_new(
        self,
        record: SourceRecord,
    ) -> tuple[Station, list[FieldConflict]]:
        station = Station(
            station_id=uuid4(),
            name=record.name,
            address=record.address,
            postal_code=record.postal_code,
            telephone=record.telephone,
            coordinates=record.coordinates,
            price=record.price,
            chargers=list(record.chargers),
        )

        station.add_source_record(record)

        return station, []

    def consolidate_into(
        self,
        station: Station,
        record: SourceRecord,
    ) -> tuple[Station, list[FieldConflict]]:
        conflicts = self._detect_conflicts(
            station,
            record,
        )

        station.add_source_record(record)
        self._merge_record(station, record)

        return station, conflicts

    def _detect_conflicts(
        self,
        station: Station,
        record: SourceRecord,
    ) -> list[FieldConflict]:
        conflicts: list[FieldConflict] = []

        self._check_field(
            conflicts,
            "name",
            station.name,
            record.name,
            station,
            record,
        )

        self._check_field(
            conflicts,
            "address",
            station.address,
            record.address,
            station,
            record,
        )

        self._check_field(
            conflicts,
            "postal_code",
            (
                station.postal_code.value
                if station.postal_code
                else None
            ),
            (
                record.postal_code.value
                if record.postal_code
                else None
            ),
            station,
            record,
        )

        self._check_field(
            conflicts,
            "telephone",
            station.telephone,
            record.telephone,
            station,
            record,
        )

        return conflicts


    def update_existing(
        self,
        station: Station,
        record: SourceRecord,
    ) -> tuple[Station, list[FieldConflict]]:
        existing_record = next(
            (
                item
                for item in station.source_records
                if item.identity == record.identity
            ),
            None,
        )

        if existing_record is None:
            return self.consolidate_into(station, record)

        conflicts = self._detect_conflicts(station, record)
        station.source_records.remove(existing_record)
        station.add_source_record(record)
        self._merge_record(station, record)

        return station, conflicts


    @staticmethod
    def _check_field(
        conflicts: list[FieldConflict],
        field_name: str,
        existing_value: object,
        new_value: object,
        station: Station,
        record: SourceRecord,
    ) -> None:
        if (
            existing_value is None
            or new_value is None
            or existing_value == new_value
        ):
            return

        existing_record = (
            station.source_records[0]
            if station.source_records
            else None
        )

        if existing_record is None:
            return

        conflicts.append(
            FieldConflict(
                field_name=field_name,
                values=(
                    ConflictValue(
                        source=existing_record.source,
                        external_id=existing_record.external_id,
                        value=existing_value,
                    ),
                    ConflictValue(
                        source=record.source,
                        external_id=record.external_id,
                        value=new_value,
                    ),
                ),
            )
        )

    @staticmethod
    def _merge_record(
        station: Station,
        record: SourceRecord,
    ) -> None:
        if station.name is None:
            station.name = record.name

        if station.address is None:
            station.address = record.address

        if station.postal_code is None:
            station.postal_code = record.postal_code

        if station.telephone is None:
            station.telephone = record.telephone

        if station.coordinates is None:
            station.coordinates = record.coordinates

        if station.price is None:
            station.price = record.price

        for charger in record.chargers:
            if charger not in station.chargers:
                station.chargers.append(charger)
