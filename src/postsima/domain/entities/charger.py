from dataclasses import dataclass

@dataclass(slots=True)
class Charger:
    connector_type: str | None
    power_kw: float | None
    quantity: int

    def __post_init__(self) -> None:
        if not self.connector_type.strip():
            raise ValueError("Connector type is required")

        # TODO: Enable when change of default values are added
        # if self.power_kw <= 0 and self.power_kw is not None:
        #     raise ValueError("Power kw is required")

        if self.quantity < 1:
            raise ValueError("Quantity must be greater than 0")
