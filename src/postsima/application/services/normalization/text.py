import re
import unicodedata

def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    value = unicodedata.normalize('NFKD', value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = value.casefold()
    value = re.sub(r"\s+", " ", value)

    return value.strip()
