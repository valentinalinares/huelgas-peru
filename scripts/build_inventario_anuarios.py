"""Construye un inventario reproducible de los anuarios MTPE 1993-2025.

El script no modifica las fuentes. Lee los libros antiguos .xls con xlrd y los
libros OOXML directamente desde sus XML internos, evitando alterar formatos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import posixpath
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import xlrd
from pypdf import PdfReader


YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
CELL_RE = re.compile(r"([A-Z]+)(\d+)")
TABLE_RE = re.compile(r"(?:CUADRO|CUADROS|C\s*[-.]?)\s*(\d+(?:[.-]\d+)?)", re.I)

TOPICS = [
    ("huelgas", ("huelga", "paralizacion")),
    ("negociacion_colectiva", ("negociacion colectiva", "negcol", "negoc", "convenio colectivo", "laudo arbitral")),
    ("planilla_electronica", ("planilla electronica", "planilla", "pla200", "planil")),
    ("registros_sindicales", ("registro sindical", "registros sindicales", "sindicato", "regsin", "regis")),
    ("empleo", ("empleo", "trabajadores registrados", "demanda laboral")),
    ("contratos_intermediacion", ("intermediacion", "tercerizacion", "contrato", "contrat")),
    ("inspeccion", ("inspeccion", "inspec")),
    ("trabajo_adolescente", ("adolescente", "trabajo infantil", "adole", "ado")),
    ("defensa_laboral", ("defensa", "patrocinio")),
    ("cese_colectivo", ("cese",)),
    ("autorizaciones", ("autori", "autorizacion")),
    ("capacitacion_programas", ("capacitacion", "programas", "facultad")),
]


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def infer_topic(*parts: object) -> str:
    text = norm(" ".join(str(p) for p in parts if p))
    for topic, needles in TOPICS:
        if any(needle in text for needle in needles):
            return topic
    return "otros"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def col_number(ref: str) -> int:
    match = CELL_RE.match(ref.upper())
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    return value


def clean_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"\s+", " ", str(value)).strip()


def excerpt(rows: list[list[object]], limit: int = 700) -> str:
    lines = []
    for row in rows:
        values = [clean_cell(value) for value in row]
        values = [value for value in values if value]
        if values:
            lines.append(" | ".join(values[:12]))
    return " || ".join(lines)[:limit]


def table_code(text: str) -> str:
    match = TABLE_RE.search(text)
    return match.group(1) if match else ""


def inspect_xls(path: Path) -> list[dict[str, object]]:
    book = xlrd.open_workbook(path, on_demand=True)
    records = []
    for name in book.sheet_names():
        sheet = book.sheet_by_name(name)
        rows = []
        for r in range(min(sheet.nrows, 18)):
            rows.append([sheet.cell_value(r, c) for c in range(min(sheet.ncols, 14))])
        text = excerpt(rows)
        records.append(
            {
                "sheet_name": name,
                "sheet_state": "visible",
                "rows": sheet.nrows,
                "columns": sheet.ncols,
                "title_excerpt": text,
                "table_code": table_code(text),
                "topic": infer_topic(path.name, name, text),
                "scan_status": "ok",
                "scan_error": "",
            }
        )
    book.release_resources()
    return records


def qname(local: str) -> str:
    return "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}" + local


def inspect_xlsx(path: Path) -> list[dict[str, object]]:
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(qname("si")):
                shared.append("".join(node.text or "" for node in item.iter(qname("t"))))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels
            if "Id" in rel.attrib and "Target" in rel.attrib
        }
        rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        records = []
        for sheet in workbook.find(qname("sheets")) or []:
            name = sheet.attrib.get("name", "")
            state = sheet.attrib.get("state", "visible")
            target = rel_map.get(sheet.attrib.get(rel_ns, ""), "")
            if target.startswith("/"):
                target = target.lstrip("/")
            else:
                target = posixpath.normpath(posixpath.join("xl", target))
            xml = ET.fromstring(archive.read(target))
            dim = xml.find(qname("dimension"))
            max_row = max_col = 0
            if dim is not None:
                last_ref = dim.attrib.get("ref", "A1").split(":")[-1]
                match = CELL_RE.match(last_ref.upper())
                if match:
                    max_col = col_number(last_ref)
                    max_row = int(match.group(2))
            preview: dict[int, dict[int, str]] = defaultdict(dict)
            sheet_data = xml.find(qname("sheetData"))
            if sheet_data is not None:
                for row in sheet_data.findall(qname("row")):
                    row_number = int(row.attrib.get("r", "0") or 0)
                    if row_number > 18:
                        continue
                    for cell in row.findall(qname("c")):
                        ref = cell.attrib.get("r", "")
                        col = col_number(ref)
                        if col <= 0 or col > 14:
                            continue
                        cell_type = cell.attrib.get("t", "")
                        value_node = cell.find(qname("v"))
                        inline_node = cell.find(qname("is"))
                        value = ""
                        if cell_type == "inlineStr" and inline_node is not None:
                            value = "".join(node.text or "" for node in inline_node.iter(qname("t")))
                        elif value_node is not None:
                            raw = value_node.text or ""
                            if cell_type == "s" and raw.isdigit() and int(raw) < len(shared):
                                value = shared[int(raw)]
                            elif cell_type == "b":
                                value = "TRUE" if raw == "1" else "FALSE"
                            else:
                                value = raw
                        preview[row_number][col] = value
            rows = []
            for row_number in sorted(preview):
                row_values = [preview[row_number].get(col, "") for col in range(1, 15)]
                rows.append(row_values)
            text = excerpt(rows)
            records.append(
                {
                    "sheet_name": name,
                    "sheet_state": state,
                    "rows": max_row,
                    "columns": max_col,
                    "title_excerpt": text,
                    "table_code": table_code(text),
                    "topic": infer_topic(path.name, name, text),
                    "scan_status": "ok",
                    "scan_error": "",
                }
            )
        return records


def source_year_map(anuarios: Path) -> dict[str, int]:
    manifest = anuarios / "manifest.generated.csv"
    mapping: dict[str, int] = {}
    if manifest.exists():
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                name = Path(row.get("zip_filename", "")).name
                if name and row.get("year", "").isdigit():
                    mapping[name.casefold()] = int(row["year"])
    # El portal reutilizó el nombre "Cuadros.zip" en 2018 y 2019. Las copias
    # descargadas quedaron diferenciadas por Windows; se conserva esa evidencia.
    mapping["cuadros.zip"] = 2018
    mapping["cuadros (1).zip"] = 2019
    mapping["cuadros (2).zip"] = 2019
    return mapping


def infer_year(path: Path, anuarios: Path, archive_years: dict[str, int]) -> int | None:
    relative = path.relative_to(anuarios)
    if relative.parts and relative.parts[0].isdigit():
        year = int(relative.parts[0])
        return year if 1993 <= year <= 2025 else None
    if relative.parts and relative.parts[0] == "_zips_originales":
        if path.name.casefold() in archive_years:
            return archive_years[path.name.casefold()]
    match = YEAR_RE.search(path.name)
    if match:
        year = int(match.group(1))
        return year if 1993 <= year <= 2025 else None
    return None


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build(root: Path) -> dict[str, object]:
    anuarios = root / "anuarios"
    output = root / "bases" / "inventario_anuarios"
    archive_years = source_year_map(anuarios)
    paths: list[Path] = []
    for child in anuarios.iterdir():
        if child.is_dir() and (child.name.isdigit() or child.name == "_zips_originales"):
            paths.extend(path for path in child.rglob("*") if path.is_file())
    paths.sort(key=lambda p: (infer_year(p, anuarios, archive_years) or 9999, p.as_posix().casefold()))

    file_rows: list[dict[str, object]] = []
    sheet_rows: list[dict[str, object]] = []
    controls: list[dict[str, object]] = []
    hashes: dict[str, list[str]] = defaultdict(list)

    for path in paths:
        year = infer_year(path, anuarios, archive_years)
        relative = path.relative_to(anuarios).as_posix()
        extension = path.suffix.lower()
        storage = "source_archive" if relative.startswith("_zips_originales/") else "year_folder"
        digest = sha256(path)
        hashes[digest].append(relative)
        file_type = {
            ".xls": "excel",
            ".xlsx": "excel",
            ".xlsm": "excel",
            ".pdf": "pdf",
            ".zip": "zip",
            ".doc": "word_legacy",
            ".docx": "word",
        }.get(extension, "other")
        status, error, pages, zip_status = "not_applicable", "", "", ""
        records: list[dict[str, object]] = []
        if file_type == "excel":
            try:
                records = inspect_xls(path) if extension == ".xls" else inspect_xlsx(path)
                status = "ok"
            except Exception as exc:  # se conserva el error en controles
                status, error = "error", f"{type(exc).__name__}: {exc}"
                controls.append({"level": "file", "control": "excel_readable", "year": year or "", "path": relative, "status": "error", "detail": error})
        elif file_type == "pdf":
            try:
                pages = len(PdfReader(path).pages)
                status = "ok"
            except Exception as exc:
                status, error = "error", f"{type(exc).__name__}: {exc}"
        elif file_type == "zip":
            try:
                with zipfile.ZipFile(path) as archive:
                    bad = archive.testzip()
                zip_status = "ok" if bad is None else f"corrupt_member:{bad}"
                status = "ok" if bad is None else "error"
            except Exception as exc:
                status, error, zip_status = "error", f"{type(exc).__name__}: {exc}", "error"
        else:
            status = "catalogued"

        file_topic = infer_topic(path.name, *(record.get("title_excerpt", "") for record in records))
        file_rows.append(
            {
                "year": year or "",
                "storage_area": storage,
                "relative_path": relative,
                "file_name": path.name,
                "extension": extension,
                "file_type": file_type,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "topic": file_topic,
                "scan_status": status,
                "scan_error": error,
                "sheet_count": len(records) if file_type == "excel" and status == "ok" else "",
                "sheet_names": " | ".join(str(record["sheet_name"]) for record in records),
                "pdf_pages": pages,
                "zip_test": zip_status,
            }
        )
        for record in records:
            sheet_rows.append(
                {
                    "year": year or "",
                    "relative_path": relative,
                    "file_name": path.name,
                    "sheet_name": record["sheet_name"],
                    "sheet_state": record["sheet_state"],
                    "rows": record["rows"],
                    "columns": record["columns"],
                    "table_code": record["table_code"],
                    "topic": record["topic"],
                    "title_excerpt": record["title_excerpt"],
                    "scan_status": record["scan_status"],
                    "scan_error": record["scan_error"],
                    "source_sha256": digest,
                }
            )

    duplicate_count = {digest: len(items) for digest, items in hashes.items()}
    for row in file_rows:
        row["duplicate_sha_count"] = duplicate_count[row["sha256"]]
    for digest, items in hashes.items():
        if len(items) > 1:
            controls.append({"level": "collection", "control": "duplicate_sha256", "year": "", "path": " | ".join(items), "status": "warning", "detail": f"{len(items)} archivos idénticos; sha256={digest}"})

    summary_rows: list[dict[str, object]] = []
    for year in range(1993, 2026):
        year_files = [row for row in file_rows if row["year"] == year and row["storage_area"] == "year_folder"]
        year_sheets = [row for row in sheet_rows if row["year"] == year]
        topics = sorted({str(row["topic"]) for row in year_sheets if row["topic"] != "otros"})
        errors = [row for row in year_files if row["scan_status"] == "error"]
        by_type = Counter(str(row["file_type"]) for row in year_files)
        summary_rows.append(
            {
                "year": year,
                "source_files": len(year_files),
                "excel_files": by_type["excel"],
                "excel_sheets": len(year_sheets),
                "pdf_files": by_type["pdf"],
                "zip_files": by_type["zip"],
                "word_files": by_type["word"] + by_type["word_legacy"],
                "other_files": by_type["other"],
                "source_archives": sum(1 for row in file_rows if row["year"] == year and row["storage_area"] == "source_archive"),
                "total_bytes": sum(int(row["bytes"]) for row in year_files),
                "topics_identified": " | ".join(topics),
                "scan_errors": len(errors),
                "inventory_status": "ok" if year_files and not errors else ("warning" if year_files else "missing"),
            }
        )
        controls.append({"level": "year", "control": "year_present", "year": year, "path": f"anuarios/{year}", "status": "ok" if year_files else "error", "detail": f"{len(year_files)} archivos en carpeta anual"})
        controls.append({"level": "year", "control": "excel_scan", "year": year, "path": f"anuarios/{year}", "status": "ok" if not errors else "error", "detail": f"{len(year_sheets)} hojas inventariadas; {len(errors)} errores"})

    write_csv(output / "inventario_archivos_1993_2025.csv", file_rows, [
        "year", "storage_area", "relative_path", "file_name", "extension", "file_type", "bytes", "sha256", "duplicate_sha_count", "topic", "scan_status", "scan_error", "sheet_count", "sheet_names", "pdf_pages", "zip_test"
    ])
    write_csv(output / "inventario_cuadros_1993_2025.csv", sheet_rows, [
        "year", "relative_path", "file_name", "sheet_name", "sheet_state", "rows", "columns", "table_code", "topic", "title_excerpt", "scan_status", "scan_error", "source_sha256"
    ])
    write_csv(output / "resumen_anual_1993_2025.csv", summary_rows, [
        "year", "source_files", "excel_files", "excel_sheets", "pdf_files", "zip_files", "word_files", "other_files", "source_archives", "total_bytes", "topics_identified", "scan_errors", "inventory_status"
    ])
    write_csv(output / "controles_inventario.csv", controls, ["level", "control", "year", "path", "status", "detail"])
    metadata = {
        "years": [1993, 2025],
        "files_catalogued": len(file_rows),
        "year_folder_files": sum(row["storage_area"] == "year_folder" for row in file_rows),
        "source_archives": sum(row["storage_area"] == "source_archive" for row in file_rows),
        "sheets_catalogued": len(sheet_rows),
        "excel_read_errors": sum(row["file_type"] == "excel" and row["scan_status"] == "error" for row in file_rows),
        "duplicate_sha_groups": sum(len(items) > 1 for items in hashes.values()),
    }
    (output / "resumen_inventario.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build(args.root.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
