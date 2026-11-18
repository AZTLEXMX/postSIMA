import argparse
import sys
from pathlib import Path

from postsima.application.models.extraction import ExtractionRequest
from postsima.domain.enums.source import Source
from postsima.infrastructure.export.excel import (
    ExcelStationExporter,
    ExcelReportLayoutExporter,
    ExcelProcessingReportExporter,
    ExcelReportFinalExporter,
)

from postsima.presentation.cli.composition import (
    REPOSITORY_OPTIONS,
    build_application,
)

SOURCE_OPTIONS = {
    "destination_charger": Source.DESTINATION_CHARGER,
    "supercharger": Source.SUPERCHARGER,
    "plugshare": Source.PLUGSHARE,
}
OUTPUT_FOLDER = Path(__file__).resolve().parents[4] / "output"
OUTPUT_RESULTS = OUTPUT_FOLDER / "estaciones.xlsx"
OUTPUT_INCIDENTS = OUTPUT_FOLDER / "incidentes.xlsx"
OUTPUT_REPORT_SS = OUTPUT_FOLDER / "report-ss.xlsx"
OUTPUT_REPORT_FINAL = OUTPUT_FOLDER / "report-final.xlsx"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postsima",
        description="Extractor y consolidador de estaciones de carga.",
    )
    parser.add_argument(
        "-s","--source",
        choices=SOURCE_OPTIONS.keys(),
        required=True,
        help="Fuente de extracción.",
    )
    parser.add_argument(
        "-f", "--ids-file",
        type=Path,
        required=True,
        help="Archivo de texto con un ID por línea (ej. input/plugshare_ids.txt).",
    )
    parser.add_argument(
        "-r", "--repository",
        choices=REPOSITORY_OPTIONS,
        default="memory",
        help="Type of data base engine. defect: memory.",
    )

    return parser


def read_ids(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de IDs: {path}")

    ids = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    return list(dict.fromkeys(ids))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        ids = read_ids(args.ids_file)
        if not ids:
            raise ValueError(f"El archivo de IDs está vacío: {args.ids_file}")

        source = SOURCE_OPTIONS[args.source]
        application = build_application(
            source=source,
            repository_type=args.repository,
        )

        result = application.execute(
            ExtractionRequest(
                source=source,
                external_ids=ids,
            )
        )

        ExcelProcessingReportExporter().export(
            result,
            OUTPUT_INCIDENTS,
        )

        report_export_result = ExcelReportLayoutExporter().export(
            result.stations,
            OUTPUT_REPORT_SS,
        )

        final_report_result = ExcelReportFinalExporter().export(
            result.stations,
            OUTPUT_REPORT_FINAL,
        )

        print("Procesamiento terminado.")
        print(f"Repositorio utilizado: {args.repository}")
        print(f"Fuente: {source.name}")
        print(f"IDs solicitados: {result.statistics.requested}")
        print(f"Registros extraídos: {result.statistics.extracted}")
        print(f"Extracciones fallidas: {result.statistics.extraction_failed}")
        print(f"Estaciones consolidadas: {len(result.stations)}")
        print(f"Coincidencias consolidadas: {result.statistics.matched}")
        print(
            f"Posibles duplicados por revisar: "
            f"{result.statistics.possible_matches}"
        )
        print(
            f"Conflictos de consolidación: "
            f"{len(result.consolidation_conflicts)}"
        )
        print(
            f"Problemas de ubicación geográfica: "
            f"{result.statistics.geographic_unresolved}"
        )
        print(
            f"Excel de incidencias, generado en: {OUTPUT_INCIDENTS}"
        )
        print(
            "Excel de formato para historial SS, generado en: "
            f"{report_export_result.output_path}"
        )
        print(
            "Excel de entrega, generado en: "
            f"{final_report_result.output_path}"
        )

        for warning in report_export_result.warnings:
            print(
                f"Advertencia del reporte: {warning}",
                file=sys.stderr,
            )

        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
