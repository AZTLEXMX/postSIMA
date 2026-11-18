import json
from pathlib import Path

from postsima.domain.enums.source import Source
from postsima.infrastructure.sources.tesla.parser import parse_tesla_location


FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "api"


def load_fixture(filename: str) -> dict:
    with (FIXTURES / filename).open(encoding="utf-8") as file:
        return json.load(file)


def test_parse_tesla_destination() -> None:
    data = load_fixture("tesla_destination.json")

    record = parse_tesla_location(
        response_json=data,
        source=Source.DESTINATION_CHARGER,
        external_id="tesla-destination-test",
    )

    assert record.source is Source.DESTINATION_CHARGER
    assert record.external_id == "tesla-destination-test"
    assert record.name == "courtyard by marriott toluca airport"
    assert record.postal_code is not None
    assert record.postal_code.value == "50200"
    assert record.telephone == "52 722 277 2020"

    assert record.coordinates is not None
    assert record.coordinates.latitude == 19.306119
    assert record.coordinates.longitude == -99.5617

    assert len(record.chargers) == 1
    assert record.chargers[0].quantity == 2
    assert record.chargers[0].power_kw == 18.0


def test_parse_tesla_supercharger() -> None:
    data = load_fixture("tesla_supercharger.json")

    record = parse_tesla_location(
        response_json=data,
        source=Source.SUPERCHARGER,
        external_id="tesla-supercharger-test",
    )

    assert record.source is Source.SUPERCHARGER
    assert record.name == "atizapan de zaragoza, em supercharger"
    assert record.postal_code is not None
    assert record.postal_code.value == "52977"

    assert record.coordinates is not None
    assert record.coordinates.latitude == 19.551248
    assert record.coordinates.longitude == -99.273039

    assert len(record.chargers) == 1
    assert record.chargers[0].quantity == 8
    assert record.chargers[0].power_kw == 75.0
