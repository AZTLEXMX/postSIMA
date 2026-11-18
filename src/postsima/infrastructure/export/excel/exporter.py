from pathlib import Path
from typing import Sequence

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from postsima.application.ports.station_exporter import ExportResult, StationExporter
from postsima.domain.entities.station import Station


class ExcelStationExporter(StationExporter):
    def export(
        self,
        stations: Sequence[Station],
        output_path: Path,
    ) -> ExportResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        stations_sheet = workbook.active
        stations_sheet.title = "Estaciones"

        self._write_stations(stations_sheet, stations)

        records_sheet = workbook.create_sheet("RegistrosFuente")
        self._write_source_records(records_sheet, stations)

        chargers_sheet = workbook.create_sheet("Cargadores")
        self._write_chargers(chargers_sheet, stations)

        for sheet in workbook.worksheets:
            self._format_sheet(sheet)

        workbook.save(output_path)

        return ExportResult(output_path=output_path)

    @staticmethod
    def _write_stations(sheet, stations: Sequence[Station]) -> None:
        headers = [
            "station_id",
            "name",
            "address",
            "postal_code",
            "telephone",
            "latitude",
            "longitude",
            "municipality",
            "state",
            "source_count",
            "sources",
        ]
        sheet.append(headers)

        for station in stations:
            sheet.append([
                str(station.station_id),
                station.name,
                station.address,
                station.postal_code.value if station.postal_code else None,
                station.telephone,
                station.coordinates.latitude if station.coordinates else None,
                station.coordinates.longitude if station.coordinates else None,
                station.municipality,
                station.state,
                len(station.source_records),
                ", ".join(sorted({
                    record.source.name
                    for record in station.source_records
                })),
            ])

    @staticmethod
    def _write_source_records(sheet, stations: Sequence[Station]) -> None:
        sheet.append([
            "station_id",
            "source",
            "source_id",
            "name",
            "address",
            "postal_code",
            "telephone",
            "latitude",
            "longitude",
            "price",
        ])

        for station in stations:
            for record in station.source_records:
                sheet.append([
                    str(station.station_id),
                    record.source.name,
                    record.external_id,
                    record.name,
                    record.address,
                    record.postal_code.value if record.postal_code else None,
                    record.telephone,
                    record.coordinates.latitude if record.coordinates else None,
                    record.coordinates.longitude if record.coordinates else None,
                    record.price,
                ])

    @staticmethod
    def _write_chargers(sheet, stations: Sequence[Station]) -> None:
        sheet.append([
            "station_id",
            "source",
            "source_id",
            "connector_type",
            "power_kw",
            "quantity",
        ])

        for station in stations:
            for record in station.source_records:
                for charger in record.chargers:
                    sheet.append([
                        str(station.station_id),
                        record.source.name,
                        record.external_id,
                        charger.connector_type,
                        charger.power_kw,
                        charger.quantity,
                    ])

    @staticmethod
    def _format_sheet(sheet) -> None:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="1F4E78",
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
            column_letter = get_column_letter(column_cells[0].column)
            sheet.column_dimensions[column_letter].width = min(
                max(max_length + 2, 12),
                45,
            )
