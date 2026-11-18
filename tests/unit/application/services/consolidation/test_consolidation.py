from uuid import uuid4

from postsima.application.services.consolidation import (
    StationConsolidator,
)
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode


def test_create_new_station() -> None:
    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="123",
        name="Estación Norte",
        coordinates=Coordinates(
            latitude=19.43,
            longitude=-99.13,
        ),
        postal_code=PostalCode("01234"),
    )

    station, conflicts = StationConsolidator().consolidate_new(record)

    assert station.station_id is not None
    assert station.name == "Estación Norte"
    assert len(station.source_records) == 1
    assert conflicts == []


def test_consolidate_record_into_existing_station() -> None:
    station = Station(
        station_id=uuid4(),
        name="Estación Norte",
        coordinates=Coordinates(
            latitude=19.43,
            longitude=-99.13,
        ),
    )

    original = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="123",
        name="Estación Norte",
    )

    station.add_source_record(original)

    new_record = SourceRecord(
        source=Source.SUPERCHARGER,
        external_id="456",
        name="Estacion Norte",
    )

    result, conflicts = StationConsolidator().consolidate_into(
        station,
        new_record,
    )

    assert result is station
    assert len(result.source_records) == 2
    assert conflicts
    assert conflicts[0].field_name == "name"


def test_missing_station_fields_are_completed() -> None:
    station = Station(
        station_id=uuid4(),
    )

    original = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="123",
    )

    station.add_source_record(original)

    new_record = SourceRecord(
        source=Source.SUPERCHARGER,
        external_id="456",
        name="Supercharger Centro",
        postal_code=PostalCode("01234"),
    )

    result, conflicts = StationConsolidator().consolidate_into(
        station,
        new_record,
    )

    assert result.name == "Supercharger Centro"
    assert result.postal_code is not None
    assert result.postal_code.value == "01234"
    assert conflicts == []