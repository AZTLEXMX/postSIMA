from pathlib import Path
from uuid import uuid4

from postsima.domain.entities.charger import Charger
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode
from postsima.infrastructure.persistence.database import (
    SqlAlchemyStationRepository,
    create_sqlite_engine,
)


def test_save_and_get_station_with_price_and_chargers(tmp_path: Path) -> None:
    engine = create_sqlite_engine(tmp_path / "test_postsima.db")
    repository = SqlAlchemyStationRepository(engine)

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="177698",
        name="7eleven - evergo",
        address="av. del estado 200",
        postal_code=PostalCode("64700"),
        telephone="+528112345678",
        coordinates=Coordinates(latitude=25.6508, longitude=-100.292454),
        price="CCS1/GBT - $8.50/kWh\nJ1772 - $7.70/kWh",
        chargers=[
            Charger(connector_type="CCS1", power_kw=50.0, quantity=1),
            Charger(connector_type="J1772", power_kw=19.0, quantity=1),
        ],
    )
    station = Station(
        station_id=uuid4(),
        name=record.name,
        address=record.address,
        postal_code=record.postal_code,
        telephone=record.telephone,
        coordinates=record.coordinates,
        municipality="Monterrey",
        state="Nuevo León",
        price=record.price,
        chargers=list(record.chargers),
    )
    station.add_source_record(record)

    repository.save(station)

    loaded = repository.get(station.station_id)
    assert loaded is not None
    assert loaded.station_id == station.station_id
    assert loaded.name == "7eleven - evergo"
    assert loaded.municipality == "Monterrey"
    assert getattr(loaded, "price", None) == "CCS1/GBT - $8.50/kWh\nJ1772 - $7.70/kWh"
    assert len(loaded.chargers) == 2
    assert len(loaded.source_records) == 1
    assert loaded.source_records[0].external_id == "177698"
    assert (
        getattr(loaded.source_records[0], "price", None)
        == "CCS1/GBT - $8.50/kWh\nJ1772 - $7.70/kWh"
    )


def test_find_by_source_record_and_avoid_source_collision(tmp_path: Path) -> None:
    engine = create_sqlite_engine(tmp_path / "test_collision.db")
    repository = SqlAlchemyStationRepository(engine)

    plugshare_record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="12345",
        name="estacion plugshare",
    )
    tesla_record = SourceRecord(
        source=Source.SUPERCHARGER,
        external_id="12345",
        name="estacion tesla",
    )

    ps_station = Station(station_id=uuid4(), name="estacion plugshare")
    ps_station.add_source_record(plugshare_record)

    tesla_station = Station(station_id=uuid4(), name="estacion tesla")
    tesla_station.add_source_record(tesla_record)

    repository.save(ps_station)
    repository.save(tesla_station)

    found_ps = repository.find_by_source_record(plugshare_record)
    found_tesla = repository.find_by_source_record(tesla_record)

    assert found_ps is not None
    assert found_tesla is not None
    assert found_ps.station_id == ps_station.station_id
    assert found_tesla.station_id == tesla_station.station_id
    assert len(repository.all()) == 2