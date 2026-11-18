from postsima.application.services.normalization import (
    normalize_coordinates,
    normalize_postal_code,
    normalize_text
)


def test_normalize_text() -> None:
    assert normalize_text("  Estación  MÉXICO  Norte ") == "estacion mexico norte"


def test_normalize_empty_text() -> None:
    assert normalize_text("   ") is None


def test_normalize_postal_code() -> None:
    assert normalize_postal_code(" 1234 ") == "01234"


def test_normalize_coordinates() -> None:
    coordinates = normalize_coordinates("19.4326", "-99.1332")

    assert coordinates is not None
    assert coordinates.latitude == 19.4326
    assert coordinates.longitude == -99.1332


def test_invalid_coordinates() -> None:
    assert normalize_coordinates("invalid", "-99.1332") is None