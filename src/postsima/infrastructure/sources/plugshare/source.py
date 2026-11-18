import time
from random import uniform
from tqdm import tqdm

from postsima.application.models.extraction import (
    ExtractionFailure,
    ExtractionRequest,
    ExtractionResult
)
from postsima.infrastructure.sources.plugshare.client import PlugShareClient
from postsima.infrastructure.sources.plugshare.parser import parse_location


class PlugShareSource:
    def __init__(
        self,
        client: PlugShareClient,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
    ) -> None:
        self._client = client
        self._min_delay = min_delay
        self._max_delay = max_delay

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        result = ExtractionResult()

        # Barra de carga
        for external_id in tqdm(
                request.external_ids,
                desc="Extrayendo estaciones | Plugshare",
                unit="estacion"
        ):
            data = self._client.get_location(external_id)

            if data is None:
                result.failures.append(
                    ExtractionFailure(
                        source=request.source,
                        external_id=external_id,
                        error_type="source_unavailable",
                        message=(
                            f"It was not possible obtain "
                            f"{external_id} from PlugShare."
                        ),
                        retryable=True
                    )
                )
                continue

            try:
                record = parse_location(data)
            except (KeyError, TypeError, ValueError) as exc:
                result.failures.append(
                    ExtractionFailure(
                        source=request.source,
                        external_id=external_id,
                        error_type="parse_error",
                        message=str(exc)
                    )
                )
                continue

            result.records.append(record)

            time.sleep(uniform(self._min_delay, self._max_delay))

        return result
