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


def extract_chargers(data: dict[str, Any]) -> list[Charger]:
    chargers: dict[tuple[str, float | None], int] = {}

    for station in data.get("stations", []):
        outlets = station.get("outlets") or []

        if outlets:
            for outlet in outlets:
                connector_type = normalize_charger_type(outlet.get("connector_name"))
                if not connector_type:
                    continue

                raw_power = outlet.get("kilowatts")
                if raw_power is None:
                    raw_power = station.get("kilowatts")

                try:
                    power_kw = float(raw_power) if raw_power is not None else None
                except (TypeError, ValueError):
                    power_kw = None

                key = (str(connector_type).strip(), power_kw)
                chargers[key] = chargers.get(key, 0) + 1

            continue

        connectors = station.get("connectors") or []
        if connectors:
            for connector in connectors:
                connector_type = normalize_charger_type(connector.get("name"))
                if not connector_type:
                    continue

                raw_power = connector.get("max_kw")
                if raw_power is None:
                    raw_power = station.get("kilowatts")

                try:
                    power_kw = float(raw_power) if raw_power is not None else None
                except (TypeError, ValueError):
                    power_kw = None

                try:
                    quantity = max(1, int(connector.get("count", 1)))
                except (TypeError, ValueError):
                    quantity = 1

                key = (str(connector_type).strip(), power_kw)
                chargers[key] = chargers.get(key, 0) + quantity

            continue

        summary = station.get("connector_summary") or {}
        for raw_connector_type, raw_quantity in summary.items():
            connector_type = normalize_charger_type(raw_connector_type)
            if not connector_type:
                continue

            try:
                quantity = max(0, int(raw_quantity))
            except (TypeError, ValueError):
                continue

            raw_power = station.get("kilowatts")
            try:
                power_kw = float(raw_power) if raw_power is not None else None
            except (TypeError, ValueError):
                power_kw = None

            key = (str(connector_type).strip(), power_kw)
            chargers[key] = chargers.get(key, 0) + quantity

    return [
        Charger(
            connector_type=connector_type,
            power_kw=power_kw,
            quantity=quantity,
        )
        for (connector_type, power_kw), quantity in sorted(
            chargers.items(),
            key=lambda item: (
                item[0][0],
                item[0][1] if item[0][1] is not None else -1,
            ),
        )
        if quantity > 0
    ]


def parse_location(data: dict[str, Any]) -> SourceRecord:
    if len(data.get("address")) <= 35:
        address = data.get("reverse_geocoded_address")
    else:
        address = data.get("address")
    components = data.get("reverse_geocoded_address_components", {})
    postal_code = normalize_postal_code(components.get("postal_code"))
    telephone = normalize_telephone_number(data.get("formatted_phone_number"))
    coordinates = normalize_coordinates(data.get("latitude"),data.get("longitude"))
    price = normalize_text(data.get("cost_description"))

    return SourceRecord(
        source=Source.PLUGSHARE,
        external_id=str(data["id"]),
        name=normalize_text(data.get("name")),
        address=normalize_text(address),
        postal_code=None if postal_code is None else PostalCode(postal_code),
        telephone=telephone,
        coordinates=coordinates,
        price=price,
        chargers=extract_chargers(data)
    )
