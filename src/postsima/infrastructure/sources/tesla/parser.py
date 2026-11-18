from typing import Any

from postsima.application.services.normalization import (
    normalize_coordinates,
    normalize_postal_code,
    normalize_text,
    normalize_telephone_number,
    normalize_charger_type
)
from postsima.domain.entities.charger import Charger
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.postal_code import PostalCode


def parse_tesla_location(response_json: dict[str, Any],
                         source: Source,
                         external_id: str) -> SourceRecord:
    data_chargers: dict[str, Any]
    data = response_json.get("data", {})
    # Important sections of JSON
    marketing = data.get("marketing", {})
    key_data = data.get("key_data", {})
    address_info = key_data.get("address", {})
    # Superchargers don't have phone number
    dc_func = data.get("destination_charger_function", {})
    sc_func = data.get("supercharger_function", {})

    address = address_info.get("formatted_address")
    if address and isinstance(address, list):
        address = address[0]
    else:
        address = address_info.get("address_1")
    postal_code = normalize_postal_code(address_info.get("postal_code"))
    telephone = (dc_func.get("phone_number") or key_data.get("phone")
                 or marketing.get("roadside_assistance_number"))
    latitude = (marketing.get("gmaps_override_latitude")
                or address_info.get("latitude"))
    longitude = (marketing.get("gmaps_override_longitude")
                 or address_info.get("longitude"))

    if sc_func and dc_func:
        data_chargers = {}
    elif sc_func:
        data_chargers = sc_func
    elif dc_func:
        data_chargers = dc_func
    else:
        data_chargers = {}

    return SourceRecord(
        source=source,
        external_id=external_id,
        name=normalize_text(marketing.get("display_name")),
        address=normalize_text(address),
        postal_code=(PostalCode(postal_code) if postal_code else None),
        telephone=normalize_telephone_number(telephone),
        coordinates=normalize_coordinates(latitude, longitude),
        chargers=_parse_chargers(data_chargers, source)
    )

def _parse_chargers(data: dict[str, Any], source: Source) -> list[Charger]:
    chargers: list[Charger] = []

    quantity = data.get("num_charger_stalls")
    power = data.get("installed_full_power")

    if source == Source.DESTINATION_CHARGER:
        connector_type = "Tesla D"
    elif source == Source.SUPERCHARGER:
        connector_type = "Tesla SC"
    else:
        connector_type = "NACS"

    if quantity is None:
        quantity = 1

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    try:
        power = float(power) if power is not None else None
    except (TypeError, ValueError):
        power = None

    chargers.append(
        Charger(
            connector_type=normalize_charger_type(connector_type),
            power_kw=power,
            quantity=max(quantity, 1)
        )
    )

    return chargers
