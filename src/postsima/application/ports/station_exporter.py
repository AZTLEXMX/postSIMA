from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from postsima.domain.entities.station import Station


@dataclass(frozen=True, slots=True)
class ExportResult:
    output_path: Path
    warnings: tuple[str, ...] = ()


class StationExporter(Protocol):
    def export(self, stations: Sequence[Station],
               output_path: Path) -> ExportResult:
        ...