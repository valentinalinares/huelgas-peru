"""Extrae las series históricas del capítulo Registro Sindical del MTPE.

Los originales se leen sin modificarlos. Se distinguen flujos de registros del
año, cancelaciones y el único stock nacional de organizaciones vigentes hallado.
"""
from pathlib import Path
import hashlib
import re
import unicodedata

import pandas as pd
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "registros_sindicales"
MONTHS = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]


def norm(value):
    text = "".join(
        c for c in unicodedata.normalize("NFD", str(value).upper())
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", text).strip()


def source(year):
    candidates = [
        p for p in (ROOT / "anuarios" / str(year)).rglob("*")
        if p.suffix.lower() in {".xls", ".xlsx"}
        and "REGISTRO SINDICAL" in norm(p.name)
    ]
    assert len(candidates) == 1, (year, candidates)
    return candidates[0]


def table_number(data):
    for value in data.iloc[:8, :8].values.ravel():
        if "CUADRO" in norm(value):
            return re.sub(r"\s+", " ", str(value)).strip()
    return ""


def find_sheet(excel, required):
    for sheet in excel.sheet_names:
        data = excel.parse(sheet, header=None)
        header = " ".join(norm(v) for v in data.iloc[:10].values.ravel() if pd.notna(v))
        if all(term in header for term in required):
            return sheet, data
    raise AssertionError((required, excel.sheet_names))


def sector(label):
    text = norm(label)
    if "MINAS Y CANTERAS" in text:
        return "mineria"
    if "MANUFACTUR" in text:
        return "manufactura"
    if text == "TOTAL":
        return "total_nacional"
    return "otra_actividad"


def extract_annual(data, year_start, year_end, columns, path, sheet):
    rows = []
    for r in range(len(data)):
        value = pd.to_numeric(data.iat[r, 2] if data.shape[1] > 2 else None, errors="coerce")
        if pd.isna(value) or int(value) < year_start or int(value) > year_end:
            continue
        record = {"anio": int(value)}
        for name, col in columns.items():
            raw = data.iat[r, col] if col < data.shape[1] else None
            record[name] = pd.to_numeric(raw, errors="coerce") if pd.notna(raw) else pd.NA
        record.update({
            "fuente_archivo": str(path.relative_to(ROOT)),
            "fuente_hoja": sheet,
            "fuente_celda": f"{get_column_letter(3)}{r+1}:{get_column_letter(max(columns.values())+1)}{r+1}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
        rows.append(record)
    result = pd.DataFrame(rows).sort_values("anio")
    assert result["anio"].tolist() == list(range(year_start, year_end + 1))
    return result


def extract_activity(year, path):
    excel = pd.ExcelFile(path)
    sheet, data = find_sheet(excel, ["SINDICATOS", "ACTIVIDAD ECONOMICA", "MES"])
    month_row = None
    month_cols = {}
    for r in range(min(15, len(data))):
        found = {norm(v): c for c, v in enumerate(data.iloc[r]) if norm(v) in MONTHS}
        if len(found) == 12:
            month_row, month_cols = r, {m: found[m] for m in MONTHS}
            break
    assert month_row is not None, (year, sheet)
    first_month_col = month_cols["ENERO"]
    # En 2002–2007 el encabezado está combinado y aparece varias columnas a la
    # izquierda de las etiquetas reales. Elegimos la columna que contiene las
    # tres filas analíticas inequívocas, no la celda visual del encabezado.
    label_col = None
    best_score = -1
    for c in range(first_month_col - 1, -1, -1):
        labels = [norm(v) for v in data.iloc[month_row + 1:, c] if pd.notna(v)]
        score = sum(any(term in value for term in ("MINAS Y CANTERAS", "MANUFACTUR", "TOTAL")) for value in labels)
        if score > best_score:
            label_col, best_score = c, score
    assert label_col is not None, (year, sheet)
    total_col = None
    for r in range(max(0, month_row - 2), month_row + 1):
        for c, value in enumerate(data.iloc[r]):
            if norm(value) == "TOTAL" and c > first_month_col:
                total_col = c
                break
    assert total_col is not None, (year, sheet)

    rows = []
    for r in range(month_row + 1, len(data)):
        label = norm(data.iat[r, label_col])
        if not label or label.startswith("FUENTE") or label.startswith("ELABORADO"):
            continue
        values = [pd.to_numeric(data.iat[r, month_cols[m]], errors="coerce") for m in MONTHS]
        published = pd.to_numeric(data.iat[r, total_col], errors="coerce")
        if all(pd.isna(v) for v in values) or pd.isna(published):
            continue
        record = {
            "anio": year,
            "actividad": re.sub(r"\s+", " ", str(data.iat[r, label_col])).strip(),
            "sector_analitico": sector(label),
        }
        for month, value in zip(MONTHS, values):
            record[month.lower()] = value
        record["total_publicado"] = published
        record["total_calculado"] = sum(values)
        record["diferencia_total"] = record["total_calculado"] - published
        record.update({
            "fuente_archivo": str(path.relative_to(ROOT)),
            "fuente_hoja": sheet,
            "fuente_celda": f"{get_column_letter(label_col+1)}{r+1}:{get_column_letter(total_col+1)}{r+1}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
        rows.append(record)
    result = pd.DataFrame(rows)
    assert set(result["sector_analitico"]) >= {"mineria", "manufactura", "total_nacional"}, (year, sheet)
    inventory = {
        "anio": year,
        "fuente_archivo": str(path.relative_to(ROOT)),
        "fuente_hoja_actividad": sheet,
        "cuadro_actividad": table_number(data),
        "filas_actividad": len(result),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return result, inventory


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    latest = source(2025)
    excel = pd.ExcelFile(latest)
    private_sheet, private_data = find_sheet(excel, ["SECTOR PRIVADO", "SEGUN ANO", "CANCELACION"])
    public_sheet, public_data = find_sheet(excel, ["SECTOR PUBLICO", "SEGUN ANO", "MODIFICACION"])

    private = extract_annual(private_data, 1993, 2025, {
        "registros_delegados": 3,
        "registros_sindicatos": 4,
        "registros_federaciones": 5,
        "reinscripcion_sindicatos": 6,
        "registros_confederaciones": 7,
        "cambios_junta_directiva": 8,
        "cancelaciones_registro_sindical": 9,
        "reformas_estatutos": 10,
    }, latest, private_sheet)
    public = extract_annual(public_data, 2004, 2025, {
        "registros_sindicatos": 3,
        "registros_federaciones": 4,
        "registros_confederaciones": 5,
        "cambios_junta_directiva": 6,
        "modificaciones_estatutos": 7,
    }, latest, public_sheet)

    activity_parts, inventory = [], []
    for year in range(2002, 2026):
        path = source(year)
        part, item = extract_activity(year, path)
        activity_parts.append(part)
        inventory.append(item)
    activity = pd.concat(activity_parts, ignore_index=True)

    stock_path = source(2002)
    stock_data = pd.read_excel(stock_path, sheet_name="C-78", header=None)
    total_row = next(r for r in range(len(stock_data)) if norm(stock_data.iat[r, 0]) == "TOTAL")
    stock = pd.DataFrame([{
        "anio": 2002,
        "ambito": "nacional",
        "organizaciones_vigentes_confederaciones": pd.to_numeric(stock_data.iat[total_row, 2]),
        "organizaciones_vigentes_federaciones": pd.to_numeric(stock_data.iat[total_row, 5]),
        "organizaciones_vigentes_sindicatos": pd.to_numeric(stock_data.iat[total_row, 8]),
        "fuente_archivo": str(stock_path.relative_to(ROOT)),
        "fuente_hoja": "C-78",
        "fuente_celda": f"A{total_row+1}:I{total_row+1}",
        "sha256": hashlib.sha256(stock_path.read_bytes()).hexdigest(),
    }])

    private_lookup = private.set_index("anio")["registros_sindicatos"]
    controls = []
    for _, row in activity.iterrows():
        controls.append({
            "control": "suma_meses_igual_total_publicado",
            "anio": row["anio"],
            "detalle": row["actividad"],
            "valor_fuente": row["total_publicado"],
            "valor_calculado": row["total_calculado"],
            "diferencia": row["diferencia_total"],
            "resultado": "ok" if row["diferencia_total"] == 0 else "revisar",
        })
    totals = activity[activity["sector_analitico"] == "total_nacional"]
    for _, row in totals.iterrows():
        expected = private_lookup.loc[row["anio"]]
        diff = row["total_publicado"] - expected
        controls.append({
            "control": "total_actividad_igual_registros_sindicatos_privados",
            "anio": row["anio"],
            "detalle": "total nacional",
            "valor_fuente": expected,
            "valor_calculado": row["total_publicado"],
            "diferencia": diff,
            "resultado": "ok" if diff == 0 else "revisar",
        })
    controls = pd.DataFrame(controls)

    coverage = pd.DataFrame([
        {"serie": "registros_sector_privado", "primer_anio": 1993, "ultimo_anio": 2025, "observaciones": 33, "nota": "Flujos anuales; incluye cancelaciones y reformas."},
        {"serie": "registros_sector_publico_ROSSP", "primer_anio": 2004, "ultimo_anio": 2025, "observaciones": 22, "nota": "Flujos anuales; no publica cancelaciones."},
        {"serie": "sindicatos_privados_por_actividad", "primer_anio": 2002, "ultimo_anio": 2025, "observaciones": len(activity), "nota": "Registros nuevos por mes y actividad; no es stock."},
        {"serie": "organizaciones_sindicales_vigentes", "primer_anio": 2002, "ultimo_anio": 2002, "observaciones": 1, "nota": "Stock nacional disponible solamente para 2002."},
    ])
    inventory = pd.DataFrame(inventory)

    private.to_csv(OUT / "registros_privados_anual.csv", index=False, encoding="utf-8-sig")
    public.to_csv(OUT / "registros_publicos_anual.csv", index=False, encoding="utf-8-sig")
    activity.to_csv(OUT / "sindicatos_privados_actividad_anual.csv", index=False, encoding="utf-8-sig")
    stock.to_csv(OUT / "organizaciones_vigentes_2002.csv", index=False, encoding="utf-8-sig")
    inventory.to_csv(OUT / "inventario_fuentes.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT / "cobertura.csv", index=False, encoding="utf-8-sig")
    controls.to_csv(OUT / "controles.csv", index=False, encoding="utf-8-sig")
    print(f"Privado: {len(private)}; público: {len(public)}; actividad: {len(activity)}; controles: {len(controls)}")


if __name__ == "__main__":
    main()
