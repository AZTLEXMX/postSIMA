from dataclasses import dataclass, field

from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.enums.source import Source


@dataclass(frozen=True, slots=True)
class ExtractionRequest:
    source: Source
    external_ids: list[str]


@dataclass(frozen=True, slots=True)
class ExtractionFailure:
    source: Source
    external_id: str
    error_type: str
    message: str
    retryable: bool = False


@dataclass(slots=True)
class ExtractionResult:
    records: list[SourceRecord] = field(default_factory=list)
    failures: list[ExtractionFailure] = field(default_factory=list)
