from math import asin, cos, radians, sin, sqrt

from postsima.application.services.normalization import normalize_text
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station


def coordinate_distance_meters(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    earth_radius = 6_371_000

    lat1 = radians(first_latitude)
    lat2 = radians(second_latitude)
    delta_lat = radians(second_latitude - first_latitude)
    delta_lon = radians(second_longitude - first_longitude)

    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    return 2 * earth_radius * asin(sqrt(value))


def coordinate_similarity(
    record: SourceRecord,
    station: Station,
) -> float | None:
    if not record.coordinates or not station.coordinates:
        return None

    distance = coordinate_distance_meters(
        record.coordinates.latitude,
        record.coordinates.longitude,
        station.coordinates.latitude,
        station.coordinates.longitude,
    )

    if distance <= 25:
        return 1.0

    if distance <= 50:
        return 0.9

    if distance <= 100:
        return 0.75

    if distance <= 200:
        return 0.5

    return 0.0

def text_similarity(
    first: str | None,
    second: str | None,
) -> float | None:
    first_normalized = normalize_text(first)
    second_normalized = normalize_text(second)

    if not first_normalized or not second_normalized:
        return None

    if first_normalized == second_normalized:
        return 1.0

    first_tokens = set(first_normalized.split())
    second_tokens = set(second_normalized.split())

    if not first_tokens or not second_tokens:
        return 0.0

    intersection = first_tokens & second_tokens
    union = first_tokens | second_tokens

    return len(intersection) / len(union)


def postal_code_similarity(
    record: SourceRecord,
    station: Station,
) -> float | None:
    if not record.postal_code or not station.postal_code:
        return None

    return (
        1.0
        if record.postal_code.value == station.postal_code.value
        else 0.0
    )
