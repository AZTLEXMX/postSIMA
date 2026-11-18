import re


def format_number(clean_number):
    formated = clean_number[:3] + " " + clean_number[3:]
    formated = formated[:7] + " " + formated[7:]

    return formated


def normalize_telephone_number(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = re.sub(r"\D", "", str(value))

    if len(normalized) == 10:
        formated_number = format_number(normalized)
        return formated_number

    elif len(normalized) == 11:
        clean_number = normalized[1:]
        formated_number = format_number(clean_number)
        new_normalized = normalized[0] + " " + formated_number
        return "0" + new_normalized

    elif len(normalized) == 12:
        clean_number = normalized[2:]
        formated_number = format_number(clean_number)
        return normalized[:2] + " " + formated_number

    elif len(normalized) == 13:
        clean_number = normalized[3:]
        formated_number = format_number(clean_number)
        return normalized[:3] + " " + formated_number

    else:
        return None
