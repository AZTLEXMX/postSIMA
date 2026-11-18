import re

CHARGER_TYPE_MAPPING: dict[str, str] = {
    # CCS
    "ccs1": "CCS1",
    "ccs 1": "CCS1",
    "ccs2": "CCS2",
    "ccs 2": "CCS2",
    # CHAdeMO
    "chademo": "CHAdeMO",
    "chademo - ccs1": "CHAdeMO / CCS1",
    "chademo-ccs1": "CHAdeMO / CCS1",
    # GB/T
    "gb/t": "GB/T",
    "gb/t(dc)": "GB/T (DC)",
    "gb/t (dc)": "GB/T (DC)",
    "gb/t (fast)": "GB/T (DC)",
    "gb/t fast": "GB/T (DC)",
    "gb/t ac": "GB/T (AC)",
    "gb/t (ac)": "GB/T (AC)",
    # J1772
    "j-1772": "J1772",
    "j1772": "J1772",
    "sae j1772": "J1772",
    "saej 1772": "J1772",
    "saej1772": "J1772",
    # Tesla / NACS
    "nacs": "NACS",
    "nacs (tesla)": "NACS",
    "tesla d": "Tesla DC",
    "tesla destination": "Tesla DC",
    "tesla sc": "Tesla SC",
    "tesla supercharger": "Tesla SC",
    "tesla (roadster)": "Tesla Roadster",
    "tesla roadster": "Tesla Roadster",
    # Type 2
    "type 2": "Type 2",
    "type2": "Type 2",
    # Tomas domésticas / industriales
    "wall": "Wall Outlet",
    "wall outlet": "Wall Outlet",
    "nema 14-50": "NEMA 14-50",
    "nema14-50": "NEMA 14-50",
    "nema tt-30": "NEMA TT-30",
    "nematt-30": "NEMA TT-30",
}


def normalize_charger_type(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = re.sub(r"\s+", " ", str(value)).strip()

    if not cleaned:
        return None

    return CHARGER_TYPE_MAPPING.get(cleaned.casefold(), cleaned)
