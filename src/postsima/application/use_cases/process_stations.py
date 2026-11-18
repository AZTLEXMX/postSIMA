from postsima.application.models.extraction import ExtractionRequest
from postsima.application.models.matching import MatchDecision
from postsima.application.models.processing import (
    ProcessingResult,
    ProcessingStatistics,
)
from postsima.application.ports.geographic_resolver import GeographicResolver
from postsima.application.ports.station_repository import StationRepository
from postsima.application.ports.station_source import StationSource
from postsima.application.services.consolidation.station_consolidator import (
    StationConsolidator,
)
from postsima.application.services.matching.matcher import StationMatcher
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.enums.source import Source
from postsima.infrastructure.persistence.memory.station_repository import (
    InMemoryStationRepository,
)


class ProcessStations:
    def __init__(
            self,
            sources: dict[Source, StationSource],
            repository: StationRepository | InMemoryStationRepository,
            consolidator: StationConsolidator,
            geographic_resolver: GeographicResolver,
    ) -> None:
        self._sources = sources
        self._repository = repository
        self._consolidator = consolidator
        self._geographic_resolver = geographic_resolver

    def execute(self, request: ExtractionRequest) -> ProcessingResult:
        result = ProcessingResult()
        result.statistics = ProcessingStatistics(
            requested=len(request.external_ids)
        )

        source = self._sources.get(request.source)
        if source is None:
            raise ValueError(
                f"No existe un adaptador para la fuente {request.source.name}."
            )

        extraction = source.extract(request)
        result.extraction_failures.extend(extraction.failures)

        result.statistics.extracted = len(extraction.records)
        result.statistics.extraction_failed = len(extraction.failures)

        for record in extraction.records:
            self._process_record(record, result)

        result.stations = self._repository.all()
        return result

    def _process_record(
        self,
        record: SourceRecord,
        result: ProcessingResult,
    ) -> None:
        existing = self._repository.find_by_source_record(record)

        if existing is not None:
            station, conflicts = self._consolidator.update_existing(
                existing, record
            )
            result.consolidation_conflicts.extend(conflicts)
            if conflicts:
                result.statistics.stations_with_conflicts += 1
            self._repository.save(station)
            self._resolve_geography(station, result)
            return


        stations = self._repository.all()
        matcher = StationMatcher(stations)
        match = matcher.match(record)

        if match.decision == MatchDecision.MATCH and match.station_id:
            station = self._repository.get(match.station_id)
            if station is not None:
                station, conflicts = self._consolidator.consolidate_into(
                    station, record
                )
                result.consolidation_conflicts.extend(conflicts)
                if conflicts:
                    result.statistics.stations_with_conflicts += 1
                result.statistics.matched += 1
                self._repository.save(station)
                self._resolve_geography(station, result)
                return

        if match.decision == MatchDecision.POSSIBLE_MATCH:
            result.matching_ambiguities.append(match)
            result.statistics.possible_matches += 1
            return

        station, conflicts = self._consolidator.consolidate_new(record)
        result.consolidation_conflicts.extend(conflicts)
        result.statistics.new_stations += 1

        self._repository.save(station)
        self._resolve_geography(station, result)

    def _resolve_geography(
        self,
        station,
        result: ProcessingResult,
    ) -> None:
        if station.coordinates is None:
            if station.station_id not in result.geographic_issues:
                result.geographic_issues.append(station.station_id)
                result.statistics.geographic_unresolved += 1
            return

        if station.municipality and station.state:
            return

        geographic_data = self._geographic_resolver.resolve(station.coordinates)

        if geographic_data is None:
            if station.station_id not in result.geographic_issues:
                result.geographic_issues.append(station.station_id)
                result.statistics.geographic_unresolved += 1
            return

        station.municipality = (
            station.municipality or geographic_data.municipality
        )
        station.state = station.state or geographic_data.state

        if station.municipality and station.state:
            result.statistics.geographic_resolved += 1
            self._repository.save(station)
        elif station.station_id not in result.geographic_issues:
            result.geographic_issues.append(station.station_id)
            result.statistics.geographic_unresolved += 1
