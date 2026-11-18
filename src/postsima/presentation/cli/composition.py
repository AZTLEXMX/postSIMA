import os
from pathlib import Path
from dotenv import load_dotenv

from postsima.application.ports.station_repository import StationRepository
from postsima.application.services.consolidation.station_consolidator import (
    StationConsolidator,
)
from postsima.application.use_cases.process_stations import ProcessStations
from postsima.domain.enums.source import Source
from postsima.infrastructure.geographic.inegi.resolver import (
    InegiGeographicResolver,
)
from postsima.infrastructure.persistence.database import (
    SqlAlchemyStationRepository,
    create_postgres_engine,
    create_sqlite_engine,
)
from postsima.infrastructure.persistence.memory.station_repository import (
    InMemoryStationRepository,
)
from postsima.infrastructure.sources.plugshare.client import PlugShareClient
from postsima.infrastructure.sources.plugshare.source import PlugShareSource
from postsima.infrastructure.sources.tesla.client import TeslaClient
from postsima.infrastructure.sources.tesla.destination import (
    TeslaDestinationSource,
)
from postsima.infrastructure.sources.tesla.supercharger import (
    TeslaSuperchargerSource,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
INEGI_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "Entidades_Estados_INEGI_Simplificado.gpkg"
)

REPOSITORY_OPTIONS = ("memory", "sqlite", "postgres")


def _build_repository(repository_type: str) -> (StationRepository |
                                                InMemoryStationRepository):
    if repository_type == "memory":
        return InMemoryStationRepository()
    if repository_type == "sqlite":
        return SqlAlchemyStationRepository(create_sqlite_engine())
    if repository_type == "postgres":
        return SqlAlchemyStationRepository(create_postgres_engine())
    raise ValueError(
        f"Repo no supported: {repository_type!r}. "
        f"Valid Options: {', '.join(REPOSITORY_OPTIONS)}."
    )


def build_application(
    source: Source,
    repository_type: str = "memory",
) -> ProcessStations:
    load_dotenv()

    if source == Source.PLUGSHARE:
        token = os.getenv("PLUGSHARE_TOKEN", "").strip()
        auth = os.getenv("PLUGSHARE_AUTH", "").strip()
        if not token or not auth:
            raise ValueError("PLUGSHARE_TOKEN or PLUGSHARE_AUTH is missing in file .env")

        source_adapter = PlugShareSource(
            client=PlugShareClient(token=token, auth=auth),
        )
    elif source in (
        Source.DESTINATION_CHARGER,
        Source.SUPERCHARGER,
    ):
        cookie = os.getenv("TESLA_COOKIE", "").strip()
        if not cookie:
            raise ValueError("TESLA_COOKIE is missing in file .env")

        tesla_client = TeslaClient(cookie=cookie)
        if source == Source.DESTINATION_CHARGER:
            source_adapter = TeslaDestinationSource(
                client=tesla_client,
            )
        else:
            source_adapter = TeslaSuperchargerSource(
                client=tesla_client,
            )
    else:
        raise ValueError(f"The Source {source!r} is NOT able to extraction.")

    repository = _build_repository(repository_type)

    return ProcessStations(
        sources={source: source_adapter},
        repository=repository,
        consolidator=StationConsolidator(),
        geographic_resolver=InegiGeographicResolver(INEGI_PATH),
    )
