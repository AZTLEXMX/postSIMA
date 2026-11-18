from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class MatchDecision(Enum):
    MATCH = "match"
    POSSIBLE_MATCH = "possible_match"
    NO_MATCH = "no_match"


class MatchFeature(Enum):
    COORDINATES = "coordinates"
    NAME = "name"
    ADDRESS = "address"
    POSTAL_CODE = "postal_code"


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    feature: MatchFeature
    description: str
    strength: float | None = None


@dataclass(frozen=True, slots=True)
class MatchCandidate:
    station_id: UUID
    score: float
    evidence: tuple[MatchEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class MatchResult:
    decision: MatchDecision
    station_id: UUID | None = None
    candidates: tuple[MatchCandidate, ...] = ()
    evidence: tuple[MatchEvidence, ...] = ()
