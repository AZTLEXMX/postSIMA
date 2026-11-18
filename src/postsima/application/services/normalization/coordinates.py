from postsima.domain.value_objects.coordinates import Coordinates

def normalize_coordinates(
        latitude: float | int | str | None,
        longitude: float | int | str | None) -> Coordinates | None:
    if latitude is None or longitude is None:
        return None

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return None

    try:
        return Coordinates(latitude=lat, longitude=lon)
    except ValueError:
        return None
