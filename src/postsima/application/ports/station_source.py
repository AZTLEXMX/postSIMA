from typing import Protocol

from postsima.application.models.extraction import (ExtractionRequest,
                                                    ExtractionResult,)


class StationSource(Protocol):
    def extract(
        self,
        request: ExtractionRequest,
    ) -> ExtractionResult:
        ...
