
from uuid import uuid4

import pytest

import postsima.application.use_cases.process_stations as process_module
from postsima.application.models.extraction import (
    ExtractionFailure,
    ExtractionRequest,
    ExtractionResult,
)
from postsima.application.models.matching import MatchDecision, MatchResult
from postsima.application.ports.geographic_resolver import GeographicData
from postsima.application.services.consolidation.station_consolidator import (
    StationConsolidator,
)
from postsima.application.use_cases.process_stations import ProcessStations
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode
from postsima.infrastructure.persistence.memory.station_repository import (
    InMemoryStationRepository,
)


def make_record(
    external_id: str = "ps-100",
    source: Source = Source.PLUGSHARE,
    name: str = "Estacion Norte",
) -> SourceRecord:
    return SourceRecord(
        source=source,
        external_id=external_id,
        name=name,
        address="Avenida Central 100",
        postal_code=PostalCode("12345"),
        coordinates=Coordinates(longitude=-70.0, latitude=40.0),
    )


class FakeSource:
    def __init__(self, result: ExtractionResult) -> None:
        self.result = result

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        return self.result


class FakeGeographicResolver:
    def resolve(self, coordinates: Coordinates) -> GeographicData:
        return GeographicData(
            municipality="Municipio de prueba",
            state="Estado de prueba",
        )


class StubMatcher:
    decision = MatchDecision.NO_MATCH

    def __init__(self, stations: list[Station]) -> None:
        self.stations = stations

    def match(self, record: SourceRecord) -> MatchResult:
        station_id = (
            self.stations[0].station_id
            if self.stations and self.decision == MatchDecision.MATCH
            else None
        )
        return MatchResult(
            decision=self.decision,
            station_id=station_id,
        )


def build_pipeline(
    source: Source,
    extraction: ExtractionResult,
    repository: InMemoryStationRepository | None = None,
) -> ProcessStations:
    return ProcessStations(
        sources={source: FakeSource(extraction)},
        repository=repository or InMemoryStationRepository(),
        consolidator=StationConsolidator(),
        geographic_resolver=FakeGeographicResolver(),
    )


def test_creates_new_station_and_resolves_geography(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(process_module, "StationMatcher", StubMatcher)
    StubMatcher.decision = MatchDecision.NO_MATCH
    record = make_record()
    pipeline = build_pipeline(
        Source.PLUGSHARE,
        ExtractionResult(records=[record]),
    )

    result = pipeline.execute(
        ExtractionRequest(Source.PLUGSHARE, [record.external_id])
    )

    assert len(result.stations) == 1
    assert len(result.stations[0].source_records) == 1
    assert result.stations[0].municipality == "Municipio de prueba"
    assert result.stations[0].state == "Estado de prueba"
    assert result.statistics.new_stations == 1
    assert result.statistics.geographic_resolved == 1


def test_consolidates_a_matching_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(process_module, "StationMatcher", StubMatcher)
    StubMatcher.decision = MatchDecision.MATCH

    original = make_record()
    station = Station(
        station_id=uuid4(),
        name=original.name,
        address=original.address,
        postal_code=original.postal_code,
        coordinates=original.coordinates,
        municipality="Municipio de prueba",
        state="Estado de prueba",
    )
    station.add_source_record(original)

    repository = InMemoryStationRepository()
    repository.save(station)

    incoming = make_record(
        external_id="tesla-200",
        source=Source.SUPERCHARGER,
    )
    pipeline = build_pipeline(
        Source.SUPERCHARGER,
        ExtractionResult(records=[incoming]),
        repository,
    )

    result = pipeline.execute(
        ExtractionRequest(Source.SUPERCHARGER, [incoming.external_id])
    )

    assert len(result.stations) == 1
    assert len(result.stations[0].source_records) == 2
    assert result.statistics.matched == 1


def test_possible_match_is_not_automatically_consolidated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(process_module, "StationMatcher", StubMatcher)
    StubMatcher.decision = MatchDecision.POSSIBLE_MATCH

    original = make_record()
    station = Station(
        station_id=uuid4(),
        name=original.name,
        coordinates=original.coordinates,
    )
    station.add_source_record(original)

    repository = InMemoryStationRepository()
    repository.save(station)

    incoming = make_record(
        external_id="ps-101",
        name="Estacion Norte sucursal",
    )
    pipeline = build_pipeline(
        Source.PLUGSHARE,
        ExtractionResult(records=[incoming]),
        repository,
    )

    result = pipeline.execute(
        ExtractionRequest(Source.PLUGSHARE, [incoming.external_id])
    )

    assert len(result.stations) == 1
    assert len(result.matching_ambiguities) == 1
    assert result.statistics.possible_matches == 1
    assert result.statistics.new_stations == 0


def test_repeated_source_record_is_updated_without_duplication() -> None:
    original = make_record()
    station = Station(
        station_id=uuid4(),
        name=original.name,
        address=original.address,
        postal_code=original.postal_code,
        coordinates=original.coordinates,
        municipality="Municipio de prueba",
        state="Estado de prueba",
    )
    station.add_source_record(original)

    repository = InMemoryStationRepository()
    repository.save(station)

    updated = make_record(name="Estacion Norte actualizada")
    pipeline = build_pipeline(
        Source.PLUGSHARE,
        ExtractionResult(records=[updated]),
        repository,
    )

    result = pipeline.execute(
        ExtractionRequest(Source.PLUGSHARE, [updated.external_id])
    )

    assert len(result.stations) == 1
    assert len(result.stations[0].source_records) == 1
    assert result.stations[0].source_records[0].name == (
        "Estacion Norte actualizada"
    )
    assert len(result.consolidation_conflicts) == 1
    assert result.statistics.stations_with_conflicts == 1


def test_extraction_failures_are_preserved() -> None:
    failure = ExtractionFailure(
        source=Source.PLUGSHARE,
        external_id="ps-failed",
        error_type="TimeoutError",
        message="La API no respondió.",
        retryable=True,
    )
    pipeline = build_pipeline(
        Source.PLUGSHARE,
        ExtractionResult(failures=[failure]),
    )

    result = pipeline.execute(
        ExtractionRequest(Source.PLUGSHARE, ["ps-failed"])
    )

    assert result.extraction_failures == [failure]
    assert result.statistics.requested == 1
    assert result.statistics.extracted == 0
    assert result.statistics.extraction_failed == 1
    assert result.stations == []


def test_unknown_source_raises_value_error() -> None:
    pipeline = ProcessStations(
        sources={},
        repository=InMemoryStationRepository(),
        consolidator=StationConsolidator(),
        geographic_resolver=FakeGeographicResolver(),
    )

    with pytest.raises(ValueError, match="No existe un adaptador"):
        pipeline.execute(
            ExtractionRequest(Source.PLUGSHARE, ["ps-100"])
        )
