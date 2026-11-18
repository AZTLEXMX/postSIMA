import pytest
import json
from pathlib import Path

from postsima.domain.enums.source import Source
from postsima.infrastructure.sources.plugshare.parser import parse_location
from postsima.application.services.normalization import normalize_charger_type


FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "api"


def load_fixture(filename: str) -> dict:
    with (FIXTURES / filename).open(encoding="utf-8") as file:
        return json.load(file)


def test_parse_plugshare_location_1() -> None:
    data = load_fixture("plugshare_location_1.json")

    record = parse_location(data)

    assert record.source is Source.PLUGSHARE
    assert record.external_id == "177698"
    assert record.name == "7eleven - evergo"
    assert record.postal_code is not None
    assert record.postal_code.value == "64700"
    assert record.coordinates is not None
    assert record.coordinates.latitude == 25.6508
    assert record.coordinates.longitude == -100.292454

    connector_types = {charger.connector_type for charger in record.chargers}
    assert connector_types == {
        "NACS",
        "CCS1",
        "GB/T (DC)",
        "J1772",
    }


def test_parse_plugshare_location_2() -> None:
    data = load_fixture("plugshare_location_2.json")

    record = parse_location(data)

    assert record.source is Source.PLUGSHARE
    assert record.external_id == "1298044"
    assert record.name == "hotel guayacan"
    assert record.postal_code is not None
    assert record.postal_code.value == "70947"
    assert record.coordinates is not None
    assert record.coordinates.latitude == 15.66471850841684
    assert record.coordinates.longitude == -96.52567125880047

    assert len(record.chargers) == 1
    assert record.chargers[0].connector_type == "J1772"
    assert record.chargers[0].quantity == 1

# Validar mapeo
@pytest.mark.parametrize(
    ("raw_name", "expected"),
    [
        ("CCS 1", "CCS1"),
        ("ccs 2", "CCS2"),
        ("chademo", "CHAdeMO"),
        ("ChadeMo-CCS1", "CHAdeMO / CCS1"),
        ("GB/T (Fast)", "GB/T (DC)"),
        ("gb/t(dc)", "GB/T (DC)"),
        ("GB/T AC", "GB/T (AC)"),
        ("J-1772", "J1772"),
        ("SAE J1772", "J1772"),
        ("NACS (Tesla)", "NACS"),
        ("Tesla D", "Tesla DC"),
        ("Tesla SC", "Tesla SC"),
        ("Tesla (Roadster)", "Tesla Roadster"),
        ("Wall", "Wall Outlet"),
        ("NEMA 14-50", "NEMA 14-50"),
        ("NEMA TT-30", "NEMA TT-30"),
    ],
)
def test_normalize_charger_type(raw_name: str, expected: str) -> None:
    assert normalize_charger_type(raw_name) == expected


def test_normalize_empty_charger_type() -> None:
    assert normalize_charger_type("   ") is None
    assert normalize_charger_type(None) is None