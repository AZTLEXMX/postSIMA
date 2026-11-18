from collections import defaultdict
from pathlib import Path
from typing import Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from postsima.application.ports.station_exporter import ExportResult
from postsima.domain.entities.charger import Charger
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station


REPORT_HEADERS = [
    "id",
    "source",
    "web_page",
    "station_name",
    "address",
    "cp",
    "town",
    "state",
    "telephone",
    "latitude",
    "longitude",
    "price",
    "electrolineras_totales",
    "cargadores_1",
    "tipo_1",
    "potencia_1",
    "cargadores_2",
    "tipo_2",
    "potencia_2",
    "cargadores_3",
    "tipo_3",
    "potencia_3",
    "cargadores_4",
    "tipo_4",
    "potencia_4",
    "cargadores_5",
    "tipo_5",
    "potencia_5",
]


class ExcelReportLayoutExporter:
    """Exporta estaciones consolidadas al formato de reporte de 28 columnas."""

    MAX_CHARGER_TYPES = 5

    def export(
        self,
        stations: Sequence[Station],
        output_path: Path,
    ) -> ExportResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Estaciones"
        sheet.append(REPORT_HEADERS)

        warnings: list[str] = []

        for station in stations:
            row, station_warnings = self._build_station_row(station)
            sheet.append(row)
            warnings.extend(station_warnings)

        self._format_sheet(sheet)
        workbook.save(output_path)

        return ExportResult(
            output_path=output_path,
            warnings=tuple(warnings),
        )

    @classmethod
    def _build_station_row(
        cls,
        station: Station,
    ) -> tuple[list[object], list[str]]:
        warnings: list[str] = []

        primary_record = cls._select_primary_source_record(
            station.source_records
        )

        # Agrega todos los registros consolidados
        # chargers = cls._aggregate_chargers(station.chargers)

        # Agrega todos los registros sin consolidar para evitar duplicados
        source_chargers = [
            charger
            for record in station.source_records
            for charger in record.chargers
        ]
        chargers_to_export = (
            source_chargers
            if source_chargers
            else station.chargers
        )
        chargers = cls._aggregate_chargers(chargers_to_export)

        if len(chargers) > cls.MAX_CHARGER_TYPES:
            omitted_types = len(chargers) - cls.MAX_CHARGER_TYPES
            warnings.append(
                f"Estación {station.station_id}: se omitieron "
                f"{omitted_types} tipos de cargador del reporte "
                "porque el formato admite un máximo de cinco."
            )

        selected_chargers = chargers[:cls.MAX_CHARGER_TYPES]

        # El total se calcula sobre todos los tipos, incluidos los que
        # no caben en las cinco posiciones del reporte.
        total_chargers = sum(
            charger.quantity for charger in chargers[:cls.MAX_CHARGER_TYPES]
        )

        row: list[object] = [
            str(station.station_id),
            int(primary_record.source) if primary_record else None,
            primary_record.external_id if primary_record else None,
            station.name,
            station.address,
            station.postal_code.value if station.postal_code else None,
            station.municipality,
            station.state,
            station.telephone,
            (
                station.coordinates.latitude
                if station.coordinates
                else None
            ),
            (
                station.coordinates.longitude
                if station.coordinates
                else None
            ),
            station.price,
            total_chargers,
        ]

        for index in range(cls.MAX_CHARGER_TYPES):
            if index < len(selected_chargers):
                charger = selected_chargers[index]
                row.extend(
                    [
                        charger.quantity,
                        charger.connector_type,
                        charger.power_kw,
                    ]
                )
            else:
                row.extend([None, None, None])

        return row, warnings

    @staticmethod
    def _select_primary_source_record(
        records: Sequence[SourceRecord],
    ) -> SourceRecord | None:
        """Elige de forma determinista la fuente representativa del reporte.

        Se prioriza el menor código numérico de Source. Si hay varios
        registros de esa fuente, se elige el menor external_id.
        """
        if not records:
            return None

        return min(
            records,
            key=lambda record: (
                int(record.source),
                record.external_id,
            ),
        )

    @staticmethod
    def _aggregate_chargers(
        chargers: Sequence[Charger],
    ) -> list[Charger]:
        """Agrupa cargadores por tipo y suma sus cantidades.

        Si un mismo tipo tiene varias potencias, se utiliza la potencia
        máxima conocida como valor representativo del reporte.
        """
        quantities: dict[str, int] = defaultdict(int)
        powers: dict[str, list[float]] = defaultdict(list)

        for charger in chargers:
            connector_type = charger.connector_type.strip()

            if not connector_type:
                continue

            quantities[connector_type] += charger.quantity

            if charger.power_kw is not None:
                powers[connector_type].append(charger.power_kw)

        aggregated = [
            Charger(
                connector_type=connector_type,
                quantity=quantity,
                power_kw=(
                    max(powers[connector_type])
                    if powers[connector_type]
                    else None
                ),
            )
            for connector_type, quantity in quantities.items()
            if quantity > 0
        ]

        # Primero los tipos con más cargadores; en empate, orden alfabético.
        return sorted(
            aggregated,
            key=lambda charger: (
                -charger.quantity,
                charger.connector_type.casefold(),
            ),
        )

    @staticmethod
    def _format_sheet(sheet) -> None:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        sheet.row_dimensions[1].height = 30

        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="1F4E78",
            )
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

        for column_cells in sheet.columns:
            max_length = max(
                (
                    len(str(cell.value))
                    for cell in column_cells
                    if cell.value is not None
                ),
                default=0,
            )

            column_letter = get_column_letter(
                column_cells[0].column
            )

            sheet.column_dimensions[column_letter].width = min(
                max(max_length + 2, 12),
                45,
            )
