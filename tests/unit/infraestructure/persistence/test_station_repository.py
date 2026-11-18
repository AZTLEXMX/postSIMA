from uuid import uuid4

from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source

from postsima.infrastructure.persistence.memory import InMemoryStationRepository

def test_save_get_stations() -> None:
    repository = InMemoryStationRepository()
    station = Station(station_id=uuid4())

    repository.save(station)

    assert repository.get(station.station_id) is station

def test_find_station_by_source_record() -> None:
    repository = InMemoryStationRepository()

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="12345",
    )

    station = Station(station_id=uuid4())
    station.add_source_record(record)

    repository.save(station)

    result = repository.find_by_source_record(record)

    assert result is station


def test_same_external_id_from_different_sources_is_not_colliding() -> None:
    repository = InMemoryStationRepository()

    plugshare_record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="12345",
    )
    tesla_record = SourceRecord(
        source=Source.SUPERCHARGER,
        external_id="12345",
    )

    plugshare_station = Station(station_id=uuid4())
    plugshare_station.add_source_record(plugshare_record)

    tesla_station = Station(station_id=uuid4())
    tesla_station.add_source_record(tesla_record)

    repository.save(plugshare_station)
    repository.save(tesla_station)

    assert repository.find_by_source_record(plugshare_record) is plugshare_station
    assert repository.find_by_source_record(tesla_record) is tesla_station
