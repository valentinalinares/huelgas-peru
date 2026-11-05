"""Extiende los cruces de negociación colectiva por actividad, 1995-2025.

Lee .xls con xlrd y .xlsx directamente desde OOXML. La selección de cuadros
parte del inventario reproducible y excluye cuadros mensuales o suprarregionales.
"""

from __future__ import annotations

import argparse
import csv
import json
import posixpath
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import xlrd


MAIN_STAGE = ("convenios colectivos", "etapas de solucion", "actividad economica")
MAIN_ORG = ("convenios colectivos", "organizacion sindical", "actividad economica")
CELL_RE = re.compile(r"([A-Z]+)(\d+)")

SECTOR_LABELS = {
    "agricultura_ganaderia_caza_silvicultura": "Agricultura, ganadería, caza y silvicultura",
    "pesca": "Pesca",
    "minas_canteras": "Explotación de minas y canteras",
    "industrias_manufactureras": "Industrias manufactureras",
    "electricidad_gas_agua": "Suministro de electricidad, gas y agua",
    "construccion": "Construcción",
    "comercio_reparacion_vehiculos": "Comercio al por mayor y menor; reparación de vehículos",
    "hoteles_restaurantes": "Hoteles y restaurantes",
    "transporte_almacenamiento_comunicaciones": "Transporte, almacenamiento y comunicaciones",
    "intermediacion_financiera": "Intermediación financiera",
    "actividades_inmobiliarias_empresariales_alquiler": "Actividades inmobiliarias, empresariales y de alquiler",
    "administracion_publica_defensa": "Administración pública y defensa",
    "ensenanza": "Enseñanza",
    "servicios_sociales_salud": "Servicios sociales y de salud",
    "otros_servicios_comunitarios_sociales_personales": "Otras actividades de servicios comunitarios, sociales y personales",
    "hogares_privados_servicio_domestico": "Hogares privados con servicio doméstico",
    "organizaciones_organos_extraterritoriales": "Organizaciones y órganos extraterritoriales",
    "total_nacional": "Total nacional",
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def as_number(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    text = str(value).strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        number = float(text)
        return int(number) if number.is_integer() else number
    return None


def sector_id(label: object) -> str | None:
    text = norm(label)
    rules = [
        ("total_nacional", ("total",)),
        ("agricultura_ganaderia_caza_silvicultura", ("agricultura",)),
        ("pesca", ("pesca",)),
        ("minas_canteras", ("minas y canteras",)),
        ("industrias_manufactureras", ("manufactur",)),
        ("electricidad_gas_agua", ("electricidad", "gas", "agua")),
        ("construccion", ("construccion",)),
        ("comercio_reparacion_vehiculos", ("comercio",)),
        ("hoteles_restaurantes", ("hoteles",)),
        ("transporte_almacenamiento_comunicaciones", ("transporte",)),
        ("intermediacion_financiera", ("intermediacion financiera",)),
        ("actividades_inmobiliarias_empresariales_alquiler", ("inmobili",)),
        ("administracion_publica_defensa", ("administracion publica",)),
        ("ensenanza", ("ensenanza",)),
        ("servicios_sociales_salud", ("servicios sociales", "salud")),
        ("otros_servicios_comunitarios_sociales_personales", ("otras activ", "comunitari")),
        ("hogares_privados_servicio_domestico", ("hogares privados",)),
        ("organizaciones_organos_extraterritoriales", ("extraterritorial",)),
    ]
    for key, needles in rules:
        if all(needle in text for needle in needles):
            return key
    return None


def column_letter(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def cell_coordinate(row: int, column: int) -> str:
    return f"{column_letter(column + 1)}{row + 1}"


def original_text(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def category_id(kind: str, header: str, last: bool) -> str:
    text = norm(header)
    if last or "total" in text:
        return "total"
    if kind == "stage":
        rules = [
            ("negociacion_directa", ("negociacion", "directa")),
            ("huelga", ("huelg",)),
            ("conciliacion", ("concili",)),
            ("extra_proceso", ("extra", "proceso")),
            ("mediacion", ("mediacion",)),
            ("autoridad_administrativa_trabajo", ("autoridad administrativa",)),
            ("arbitraje_acuerdo_partes", ("acuerdo", "partes")),
            ("arbitraje_unipersonal", ("unipersonal",)),
            ("arbitraje_potestativo", ("potestativo",)),
            ("arbitraje_obligatorio", ("obligatorio",)),
            ("arbitraje_auto_directoral_general", ("auto directoral general",)),
            ("arbitraje_resolucion_subdirectoral", ("subdirectoral",)),
            ("arbitraje_resolucion_directoral", ("directoral",)),
            ("arbitraje_resolucion_ministerial", ("ministerial",)),
            ("arbitraje_no_indica", ("no indica",)),
        ]
    else:
        rules = [
            ("federacion", ("federacion",)),
            ("sindicato_obreros", ("sindicato", "obreros")),
            ("sindicato_empleados", ("sindicato", "empleados")),
            ("sindicato_unico", ("sindicato", "unico")),
            ("comite_sindical", ("comite", "sindical")),
            ("delegados_empleados_obreros", ("delegados", "empleados / obreros")),
            ("delegados_empleados", ("delegados", "empleados")),
            ("delegados_obreros", ("delegados", "obreros")),
        ]
    for key, needles in rules:
        if all(needle in text for needle in needles):
            return key
    raise ValueError(f"Categoría {kind} no reconocida: {header!r}")


def col_number(ref: str) -> int:
    match = CELL_RE.match(ref.upper())
    if not match:
        return 0
    result = 0
    for char in match.group(1):
        result = result * 26 + ord(char) - 64
    return result


def qname(local: str) -> str:
    return "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}" + local


def read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[object]]:
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(qname("si")):
                shared.append("".join(node.text or "" for node in item.iter(qname("t"))))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels if "Id" in rel.attrib}
        rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        selected = None
        for sheet in workbook.find(qname("sheets")) or []:
            if sheet.attrib.get("name") == sheet_name:
                selected = rel_map[sheet.attrib[rel_ns]]
                break
        if selected is None:
            raise KeyError(f"No existe hoja {sheet_name!r} en {path.name}")
        target = selected.lstrip("/") if selected.startswith("/") else posixpath.normpath(posixpath.join("xl", selected))
        xml = ET.fromstring(archive.read(target))
        values: dict[int, dict[int, object]] = defaultdict(dict)
        max_row = max_col = 0
        sheet_data = xml.find(qname("sheetData"))
        if sheet_data is None:
            return []
        for row in sheet_data.findall(qname("row")):
            rnum = int(row.attrib.get("r", "0") or 0)
            max_row = max(max_row, rnum)
            for cell in row.findall(qname("c")):
                ref = cell.attrib.get("r", "")
                cnum = col_number(ref)
                max_col = max(max_col, cnum)
                ctype = cell.attrib.get("t", "")
                raw_node = cell.find(qname("v"))
                inline_node = cell.find(qname("is"))
                value: object = ""
                if ctype == "inlineStr" and inline_node is not None:
                    value = "".join(node.text or "" for node in inline_node.iter(qname("t")))
                elif raw_node is not None:
                    raw = raw_node.text or ""
                    if ctype == "s" and raw.isdigit() and int(raw) < len(shared):
                        value = shared[int(raw)]
                    elif ctype == "b":
                        value = raw == "1"
                    elif ctype in {"str", "e"}:
                        value = raw
                    else:
                        value = as_number(raw) if as_number(raw) is not None else raw
                values[rnum][cnum] = value
        return [[values[r].get(c, "") for c in range(1, max_col + 1)] for r in range(1, max_row + 1)]


def read_sheet(path: Path, sheet_name: str) -> list[list[object]]:
    if path.suffix.lower() == ".xls":
        book = xlrd.open_workbook(path, on_demand=True)
        sheet = book.sheet_by_name(sheet_name)
        matrix = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
        book.release_resources()
        return matrix
    return read_xlsx_sheet(path, sheet_name)


def pick_sources(root: Path) -> dict[int, dict[str, object]]:
    inventory = root / "bases" / "inventario_anuarios" / "inventario_cuadros_1993_2025.csv"
    candidates: dict[int, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    with inventory.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if not row["year"].isdigit() or not (1995 <= int(row["year"]) <= 2025):
                continue
            text = norm(row["title_excerpt"])
            if not ("nivel nacional" in text or "peru" in text):
                continue
            if text.startswith("listado"):
                continue
            if "segun meses" in text or "segun mes" in text or "caracter supra" in text:
                continue
            if all(term in text for term in MAIN_STAGE):
                candidates[int(row["year"])]["stage"].append(row)
            if all(term in text for term in MAIN_ORG):
                candidates[int(row["year"])]["org"].append(row)
    selected: dict[int, dict[str, object]] = {}
    for year in range(1995, 2026):
        selected[year] = {}
        for kind in ("stage", "org"):
            rows = candidates[year][kind]
            if len(rows) != 1:
                raise RuntimeError(f"{year} {kind}: se esperaba un cuadro principal, hallados {len(rows)}: {[(r['file_name'], r['sheet_name']) for r in rows]}")
            row = rows[0]
            selected[year][kind] = {
                "path": root / "anuarios" / row["relative_path"],
                "relative_path": row["relative_path"],
                "sheet": row["sheet_name"],
                "title": row["title_excerpt"],
            }
    return selected


def detect_table(matrix: list[list[object]], kind: str) -> tuple[list[int], list[tuple[int, str, str]], int, list[str]]:
    total_candidates: list[tuple[int, int]] = []
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            if norm(value).startswith("total") and any(str(item).strip() and (as_number(item) is not None or str(item).strip() in {"-", "--"}) for item in row[c + 1 :]):
                total_candidates.append((r, c))
    if not total_candidates:
        raise ValueError("No se encontró la fila TOTAL con datos")
    total_row, total_label_col = total_candidates[-1]
    total_values = matrix[total_row]
    data_columns = [c for c in range(total_label_col + 1, len(total_values)) if str(total_values[c]).strip() != ""]
    if len(data_columns) < 2:
        raise ValueError(f"Fila TOTAL sin columnas suficientes: {total_values}")
    first_data_col = data_columns[0]

    activities: list[tuple[int, str, str]] = []
    for r in range(total_row):
        before = [(c, value) for c, value in enumerate(matrix[r][:first_data_col]) if isinstance(value, str) and value.strip()]
        if not before:
            continue
        label = before[-1][1]
        sid = sector_id(label)
        if sid and sid != "total_nacional" and any(c < len(matrix[r]) and str(matrix[r][c]).strip() != "" for c in data_columns):
            activities.append((r, sid, str(label).strip()))
    if not activities:
        raise ValueError("No se detectaron filas de actividad")
    activities.append((total_row, "total_nacional", str(matrix[total_row][total_label_col]).strip()))
    first_activity_row = min(item[0] for item in activities)

    categories: list[str] = []
    for index, c in enumerate(data_columns):
        parts = []
        for r in range(first_activity_row):
            if c < len(matrix[r]) and isinstance(matrix[r][c], str) and matrix[r][c].strip():
                parts.append(matrix[r][c].strip())
        header = " | ".join(parts)
        categories.append(category_id(kind, header, index == len(data_columns) - 1))
    if len(categories) != len(set(categories)):
        raise ValueError(f"Categorías duplicadas en {kind}: {categories}")
    return data_columns, activities, total_row, categories


def extract_one(year: int, kind: str, source: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    matrix = read_sheet(source["path"], source["sheet"])
    data_columns, activities, total_row, categories = detect_table(matrix, kind)
    title_text = " ".join(str(value) for row in matrix[:12] for value in row if isinstance(value, str) and value.strip())
    code_match = re.search(r"cuadro\s*(?:n[^\d]*)?(\d+)", norm(title_text))
    table_code = f"C-{code_match.group(1)}" if code_match else str(source["sheet"])
    notes = " ".join(
        str(value).strip()
        for row in matrix[total_row + 1 : total_row + 12]
        for value in row
        if isinstance(value, str) and ("nota" in norm(value) or "incluye" in norm(value) or "excluye" in norm(value))
    )
    records: list[dict[str, object]] = []
    for r, sid, raw_label in activities:
        for index, (c, category) in enumerate(zip(data_columns, categories)):
            raw = matrix[r][c] if c < len(matrix[r]) else ""
            numeric = as_number(raw)
            state = "numerico" if numeric is not None else ("simbolo_fuente_sin_interpretar" if str(raw).strip() else "celda_vacia")
            record_note = notes
            if sid == "minas_canteras":
                record_note = (record_note + " La categoría Explotación de minas y canteras no equivale exactamente a minería metálica; contratistas mineros pueden figurar en otras actividades.").strip()
            records.append(
                {
                    "anio": year,
                    "sector_id": sid,
                    "actividad_economica": SECTOR_LABELS[sid],
                    "actividad_original_mtpe": raw_label,
                    "categoria": category,
                    "valor": int(numeric) if numeric is not None and float(numeric).is_integer() else (numeric if numeric is not None else ""),
                    "valor_original": original_text(raw),
                    "estado_valor": state,
                    "unidad": "convenios colectivos",
                    "fuente_documento": Path(source["path"]).name,
                    "fuente_relativa": source["relative_path"],
                    "hoja": source["sheet"],
                    "cuadro": table_code,
                    "celda": cell_coordinate(r, c),
                    "nota": record_note,
                }
            )
    metadata = {
        "anio": year,
        "dimension": "etapas_solucion" if kind == "stage" else "organizacion_sindical",
        "fuente_relativa": source["relative_path"],
        "hoja": source["sheet"],
        "cuadro": table_code,
        "actividades_mas_total": len(activities),
        "categorias_incluido_total": len(categories),
        "filas_extraidas": len(records),
        "categorias": " | ".join(categories),
        "nota_fuente": notes,
    }
    return records, metadata


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate(stage_rows: list[dict[str, object]], org_rows: list[dict[str, object]], root: Path) -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []

    def add(control: str, year: int, key: str, observed: object, expected: object, status: str, detail: str = "") -> None:
        controls.append({"control": control, "anio": year, "clave": key, "observado": observed, "referencia": expected, "resultado": status, "detalle": detail})

    for kind, rows in (("etapas", stage_rows), ("organizacion", org_rows)):
        grouped: dict[tuple[int, str], list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[(int(row["anio"]), str(row["sector_id"]))].append(row)
        for (year, sid), group in grouped.items():
            total = next(row for row in group if row["categoria"] == "total")
            components = [row for row in group if row["categoria"] != "total"]
            numeric_sum = sum(int(row["valor"]) for row in components if row["valor"] != "")
            symbols = sum(row["valor"] == "" for row in components)
            expected = total["valor"]
            if expected == "":
                status = "no_evaluable_simbolo_total"
            elif symbols and numeric_sum < int(expected):
                status = "suma_parcial_por_simbolos"
            else:
                status = "coincide" if numeric_sum == int(expected) else "revisar_fuente"
            add(f"suma_categorias_{kind}", year, sid, numeric_sum, expected, status, f"{symbols} componentes no numéricos conservados")

    def totals(rows: list[dict[str, object]]) -> dict[tuple[int, str], int]:
        return {(int(row["anio"]), str(row["sector_id"])): int(row["valor"]) for row in rows if row["categoria"] == "total" and row["valor"] != ""}

    stage_totals, org_totals = totals(stage_rows), totals(org_rows)
    for key in sorted(set(stage_totals) | set(org_totals)):
        observed, expected = stage_totals.get(key), org_totals.get(key)
        status = "no_evaluable_simbolo_fuente" if observed is None or expected is None else ("coincide" if observed == expected else "revisar_fuente")
        add("total_etapas_vs_organizacion", key[0], key[1], observed, expected, status)

    c56_path = root / "bases" / "negociacion_colectiva" / "base_negociacion_colectiva_c56_1995_2025.csv"
    with c56_path.open(encoding="utf-8-sig", newline="") as handle:
        c56 = {(int(row["anio"]), row["sector_id"]): int(float(row["convenios_colectivos"])) for row in csv.DictReader(handle)}
    for key, expected in sorted(c56.items()):
        observed = stage_totals.get(key)
        status = "no_evaluable_simbolo_fuente" if observed is None else ("coincide" if observed == expected else "revisar_fuente")
        add("total_cruce_vs_C56", key[0], key[1], observed, expected, status)
    return controls


def build(root: Path) -> dict[str, object]:
    sources = pick_sources(root)
    stage_rows: list[dict[str, object]] = []
    org_rows: list[dict[str, object]] = []
    inventory: list[dict[str, object]] = []
    for year in range(1995, 2026):
        try:
            rows, meta = extract_one(year, "stage", sources[year]["stage"])
        except Exception as exc:
            raise RuntimeError(f"Error extrayendo {year} stage: {exc}") from exc
        stage_rows.extend(rows)
        inventory.append(meta)
        try:
            rows, meta = extract_one(year, "org", sources[year]["org"])
        except Exception as exc:
            raise RuntimeError(f"Error extrayendo {year} org: {exc}") from exc
        org_rows.extend(rows)
        inventory.append(meta)
    controls = validate(stage_rows, org_rows, root)
    discrepancies = [row for row in controls if row["resultado"] == "revisar_fuente"]
    if discrepancies:
        raise RuntimeError(f"Controles con discrepancia: {discrepancies[:10]}")

    out = root / "bases" / "negociacion_colectiva" / "complementos"
    data_fields = ["anio", "sector_id", "actividad_economica", "actividad_original_mtpe", "categoria", "valor", "valor_original", "estado_valor", "unidad", "fuente_documento", "fuente_relativa", "hoja", "cuadro", "celda", "nota"]
    write_csv(out / "etapas_por_actividad_1995_2025.csv", stage_rows, data_fields)
    write_csv(out / "organizacion_por_actividad_1995_2025.csv", org_rows, data_fields)
    write_csv(out / "inventario_cruces_historicos_1995_2025.csv", inventory, ["anio", "dimension", "fuente_relativa", "hoja", "cuadro", "actividades_mas_total", "categorias_incluido_total", "filas_extraidas", "categorias", "nota_fuente"])
    write_csv(out / "controles_cruces_historicos.csv", controls, ["control", "anio", "clave", "observado", "referencia", "resultado", "detalle"])

    priority = [row for row in stage_rows + org_rows if row["sector_id"] in {"minas_canteras", "industrias_manufactureras", "total_nacional"}]
    for row in priority:
        row["dimension"] = "etapas_solucion" if row in stage_rows else "organizacion_sindical"
    priority.sort(key=lambda row: (int(row["anio"]), row["dimension"], row["sector_id"], row["categoria"]))
    write_csv(out / "serie_prioritaria_cruces_1995_2025.csv", priority, ["anio", "dimension", *data_fields[1:]])
    summary = {
        "years": [1995, 2025],
        "stage_rows": len(stage_rows),
        "organization_rows": len(org_rows),
        "priority_rows": len(priority),
        "source_tables": len(inventory),
        "controls": len(controls),
        "discrepancies": len(discrepancies),
        "non_evaluable_symbol_controls": sum(str(row["resultado"]).startswith("no_evaluable") for row in controls),
        "partial_symbol_controls": sum(row["resultado"] == "suma_parcial_por_simbolos" for row in controls),
    }
    (out / "resumen_cruces_historicos.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def print_inspection(root: Path, years: list[int]) -> None:
    sources = pick_sources(root)
    for year in years:
        for kind in ("stage", "org"):
            source = sources[year][kind]
            matrix = read_sheet(source["path"], source["sheet"])
            print(f"\n### {year} {kind} | {source['relative_path']} | {source['sheet']}")
            for index, row in enumerate(matrix[:32], 1):
                visible = [f"{col}:{value}" for col, value in enumerate(row, 1) if str(value).strip() != ""]
                if visible:
                    print(index, " | ".join(visible[:20]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--inspect-years", default="")
    args = parser.parse_args()
    root = args.root.resolve()
    sources = pick_sources(root)
    if args.inspect_years:
        print_inspection(root, [int(value) for value in args.inspect_years.split(",")])
    else:
        print(json.dumps(build(root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
