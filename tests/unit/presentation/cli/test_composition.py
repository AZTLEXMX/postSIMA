from pathlib import Path
import pytest

from postsima.domain.enums.source import Source
from postsima.presentation.cli import composition

FIXTURES = Path(__file__).resolve().parents[4] / "data" / "reference"
inegi_path = Path(FIXTURES, "Entidades_Estados_INEGI_Simplificado.gpkg")

@pytest.mark.parametrize(
    ("source", "expected_adapter"),
    [
        (Source.PLUGSHARE, "PlugShareSource"),
        (Source.DESTINATION_CHARGER, "TeslaDestinationSource"),
        (Source.SUPERCHARGER, "TeslaSuperchargerSource"),
    ],
)
def test_build_application_selects_source_adapter(
    monkeypatch,
    source,
    expected_adapter,
):
    monkeypatch.setenv("PLUGSHARE_TOKEN", "test-token")
    monkeypatch.setenv("TESLA_COOKIE", "test-cookie")

    class FakeDependency:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(composition, "PlugShareClient", FakeDependency)
    monkeypatch.setattr(composition, "TeslaClient", FakeDependency)
    monkeypatch.setattr(composition, "InegiGeographicResolver", FakeDependency)

    application = composition.build_application(
        source=source,
    )

    assert source in application._sources
    assert type(application._sources[source]).__name__ == expected_adapter
