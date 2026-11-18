from dataclasses import dataclass
from typing import Any

from postsima.domain.enums.source import Source


@dataclass(frozen=True, slots=True)
class ConflictValue:
    source: Source
    external_id: str
    value: Any


@dataclass(frozen=True, slots=True)
class FieldConflict:
    field_name: str
    values: tuple[ConflictValue, ...]


@dataclass(frozen=True, slots=True)
class ConsolidationResult:
    conflicts: tuple[FieldConflict, ...] = ()
