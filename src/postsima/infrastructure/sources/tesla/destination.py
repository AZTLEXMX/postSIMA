import time
from random import uniform
from tqdm import tqdm

from postsima.application.models.extraction import (
    ExtractionFailure,
    ExtractionRequest,
    ExtractionResult
)
from postsima.domain.enums.source import Source
from postsima.infrastructure.sources.tesla.client import TeslaClient
from postsima.infrastructure.sources.tesla.parser import parse_tesla_location


class TeslaDestinationSource:
    def __init__(
        self,
        client: TeslaClient,
        min_delay: float = 2.0,
        max_delay: float = 4.0,
    ) -> None:
        self._client = client
        self._min_delay = min_delay
        self._max_delay = max_delay

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        result = ExtractionResult()

        for external_id in tqdm(
                request.external_ids,
                desc="Extrayendo estaciones | Tesla DC",
                unit="estacion"
        ):
            data = self._client.get_destination(external_id)

            if data is None:
                result.failures.append(
                    ExtractionFailure(
                        source=Source.DESTINATION_CHARGER,
                        external_id=external_id,
                        error_type="source_unavailable",
                        message=(
                            f"It was not possible obtain "
                            f"Destination {external_id} from Tesla."
                        ),
                        retryable=True,
                    )
                )
                continue

            try:
                record = parse_tesla_location(
                    response_json=data,
                    source=Source.DESTINATION_CHARGER,
                    external_id=external_id,
                )
            except (KeyError, TypeError, ValueError) as exc:
                result.failures.append(
                    ExtractionFailure(
                        source=Source.DESTINATION_CHARGER,
                        external_id=external_id,
                        error_type="parse_error",
                        message=str(exc),
                    )
                )
                continue

            result.records.append(record)

            time.sleep(uniform(self._min_delay, self._max_delay,))

        return result
