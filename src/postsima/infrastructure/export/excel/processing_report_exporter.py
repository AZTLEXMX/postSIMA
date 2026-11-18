from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from postsima.application.models.processing import ProcessingResult


class ExcelProcessingReportExporter:
    def export(self, result: ProcessingResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        summary = workbook.active
        summary.title = "Resumen"

        stats = result.statistics
        summary.append(["Indicador", "Cantidad"])
        for label, value in (
            ("Solicitados", stats.requested),
            ("Extraídos", stats.extracted),
            ("Extracciones fallidas", stats.extraction_failed),
            ("Coincidencias consolidadas", stats.matched),
            ("Coincidencias posibles", stats.possible_matches),
            ("Estaciones nuevas", stats.new_stations),
            ("Estaciones con conflictos", stats.stations_with_conflicts),
            ("Geografía resuelta", stats.geographic_resolved),
            ("Geografía sin resolver", stats.geographic_unresolved),
        ):
            summary.append([label, value])

        failures = workbook.create_sheet("ErroresExtraccion")
        failures.append([
            "source", "external_id", "error_type", "message", "retryable",
        ])
        for item in result.extraction_failures:
            failures.append([
                item.source.name,
                item.external_id,
                item.error_type,
                item.message,
                item.retryable,
            ])

        ambiguities = workbook.create_sheet("CoincidenciasPosibles")
        ambiguities.append([
            "decision", "station_id", "candidate_station_id",
            "score", "evidence",
        ])
        for match in result.matching_ambiguities:
            candidates = match.candidates or (None,)
            for candidate in candidates:
                ambiguities.append([
                    match.decision.value,
                    str(match.station_id) if match.station_id else None,
                    str(candidate.station_id) if candidate else None,
                    candidate.score if candidate else None,
                    "; ".join(
                        f"{e.feature.value}: {e.description}"
                        for e in (candidate.evidence if candidate else match.evidence)
                    ),
                ])

        conflicts = workbook.create_sheet("Conflictos")
        conflicts.append([
            "field_name", "source", "external_id", "value",
        ])
        for conflict in result.consolidation_conflicts:
            for item in conflict.values:
                conflicts.append([
                    conflict.field_name,
                    item.source.name,
                    item.external_id,
                    str(item.value) if item.value is not None else None,
                ])

        geographic = workbook.create_sheet("GeografiaPendiente")
        geographic.append(["station_id"])
        for station_id in result.geographic_issues:
            geographic.append([str(station_id)])

        for sheet in workbook.worksheets:
            self._format_sheet(sheet)

        workbook.save(output_path)
        return output_path

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

        for cells in sheet.columns:
            width = max(
                (len(str(cell.value)) for cell in cells if cell.value is not None),
                default=0,
            )
            letter = get_column_letter(cells[0].column)
            sheet.column_dimensions[letter].width = min(max(width + 2, 12), 60)
