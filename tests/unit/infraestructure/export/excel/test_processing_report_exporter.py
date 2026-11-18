from openpyxl import load_workbook

from postsima.application.models.processing import ProcessingResult
from postsima.infrastructure.export.excel.processing_report_exporter import (
    ExcelProcessingReportExporter,
)


def test_exports_processing_report(tmp_path):
    output = tmp_path / "reports" / "processing.xlsx"

    ExcelProcessingReportExporter().export(
        ProcessingResult(),
        output,
    )

    assert output.exists()

    workbook = load_workbook(output, read_only=True)
    assert workbook.sheetnames == [
        "Resumen",
        "ErroresExtraccion",
        "CoincidenciasPosibles",
        "Conflictos",
        "GeografiaPendiente",
    ]

    assert workbook["Resumen"]["A1"].value == "Indicador"
    assert workbook["ErroresExtraccion"]["A1"].value == "source"
    workbook.close()
