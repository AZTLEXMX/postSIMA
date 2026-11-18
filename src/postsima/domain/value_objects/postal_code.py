from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PostalCode:
    value: str

    def __post_init__(self) -> None:
        value = self.value.strip()

        if not value.isdigit():
            raise ValueError("Postal Code only has digits")

        object.__setattr__(self, "value", value)
