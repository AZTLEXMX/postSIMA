from datetime import date, timedelta

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
    "cons",
    "fecha_lev",
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


class ExcelReportFinalExporter:
    MAX_CHARGER_TYPES = 5

    def export(
        self,
        stations: Sequence[Station],
        output_path: Path,
    ) -> ExportResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Electrolineras"
        sheet.append(REPORT_HEADERS)

        hoy = date.today()
        ultimo_dia_mes_anterior = hoy.replace(day=1) - timedelta(days=1)
        # Caso febrero
        dia = 27 if ultimo_dia_mes_anterior.month == 2 else 30
        fecha_resultado = ultimo_dia_mes_anterior.replace(day=dia)
        fecha_levantamiento = fecha_resultado.strftime("%d-%m-%Y")

        for counter, station in enumerate(stations, start=1):
            row = self._build_station_row(station,
                                                            counter,
                                                            fecha_levantamiento)
            sheet.append(row)

        self._format_sheet(sheet)
        workbook.save(output_path)

        return ExportResult(
            output_path=output_path
        )

    @classmethod
    def _build_station_row(
        cls,
        station: Station,
        counter_station: int,
        fecha_lev: str,
    ) -> list[object]:
        primary_record = cls._select_primary_source_record(
            station.source_records
        )

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

        selected_chargers = chargers[:cls.MAX_CHARGER_TYPES]

        total_chargers = sum(
            charger.quantity for charger in chargers[:cls.MAX_CHARGER_TYPES]
        )

        row: list[object] = [
            counter_station,
            fecha_lev,
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

        return row

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
            cell.font = Font(bold=True, color="000000")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="FFFFFF",
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
