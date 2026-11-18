import re

def normalize_postal_code(value: str | int | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    if not normalized:
        return None

    normalized = re.sub(r"\D", "", normalized)

    if not normalized:
        return None

    return normalized.zfill(5)
