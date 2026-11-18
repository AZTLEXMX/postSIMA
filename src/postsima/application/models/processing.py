from dataclasses import dataclass, field
from uuid import UUID

from postsima.application.models.consolidation import FieldConflict
from postsima.application.models.extraction import ExtractionFailure
from postsima.application.models.matching import MatchResult
from postsima.domain.entities.station import Station


@dataclass(slots=True)
class ProcessingStatistics:
    requested: int = 0
    extracted: int = 0
    extraction_failed: int = 0
    matched: int = 0
    possible_matches: int = 0
    new_stations: int = 0
    stations_with_conflicts: int = 0
    geographic_resolved: int = 0
    geographic_unresolved: int = 0


@dataclass(slots=True)
class ProcessingResult:
    stations: list[Station] = field(default_factory=list)
    extraction_failures: list[ExtractionFailure] = field(default_factory=list)
    matching_ambiguities: list[MatchResult] = field(default_factory=list)
    consolidation_conflicts: list[FieldConflict] = field(default_factory=list)
    geographic_issues: list[UUID] = field(default_factory=list)
    statistics: ProcessingStatistics = field(
        default_factory=ProcessingStatistics
    )
