from uuid import uuid4

from postsima.application.models.matching import MatchDecision
from postsima.application.services.matching import StationMatcher
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode


def test_matching_by_close_coordinates_and_same_name() -> None:
    station = Station(
        station_id=uuid4(),
        name="Cafe Sierra Norte",
        coordinates=Coordinates(
            latitude=25.2866652,
            longitude=-100.0345202,
        ),
        postal_code=PostalCode("67350"),
    )

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="166237",
        name="Cafe Sierra Norte",
        coordinates=Coordinates(
            latitude=25.28676309474127,
            longitude=-100.03442595948982,
        ),
        postal_code=PostalCode("67350"),
    )

    result = StationMatcher([station]).match(record)

    assert result.decision is MatchDecision.MATCH
    assert result.station_id == station.station_id


def test_same_external_id_from_other_source_can_match() -> None:
    station = Station(
        station_id=uuid4(),
        name="Temascalcingo, MEX",
        coordinates=Coordinates(
            latitude=19.8562695,
            longitude=-100.0426142
        ),
    )

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="122596",
        name="Temascalcingo",
        coordinates=Coordinates(
            latitude=19.8563369545,
            longitude=-100.0430259153
        ),
    )

    result = StationMatcher([station]).match(record)

    assert result.decision is MatchDecision.MATCH


def test_different_ids_from_same_source_never_match() -> None:
    station = Station(
        station_id=uuid4(),
        name="Estación de prueba",
        coordinates=Coordinates(
            latitude=19.4326,
            longitude=-99.1332,
        ),
        source_records=[
            SourceRecord(
                source=Source.PLUGSHARE,
                external_id="1234",
                name="Estación de prueba",
                coordinates=Coordinates(
                    latitude=19.4326,
                    longitude=-99.1332,
                ),
            )
        ],
    )

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="12345",
        name="Estación de prueba",
        coordinates=Coordinates(
            latitude=19.4326,
            longitude=-99.1332,
        ),
    )

    result = StationMatcher([station]).match(record)

    assert result.decision is MatchDecision.NO_MATCH
    assert result.station_id is None


def test_records_from_different_sources_can_match() -> None:
    station = Station(
        station_id=uuid4(),
        name="Estación de prueba",
        coordinates=Coordinates(
            latitude=19.4326,
            longitude=-99.1332,
        ),
        source_records=[
            SourceRecord(
                source=Source.DESTINATION_CHARGER,
                external_id="4575",
                name="Estación de prueba",
                coordinates=Coordinates(
                    latitude=19.4326,
                    longitude=-99.1332,
                ),
            )
        ],
    )

    record = SourceRecord(
        source=Source.PLUGSHARE,
        external_id="1234",
        name="Estación de prueba",
        coordinates=Coordinates(
            latitude=19.4326,
            longitude=-99.1332,
        ),
    )

    result = StationMatcher([station]).match(record)

    assert result.decision is MatchDecision.MATCH
    assert result.station_id == station.station_id
