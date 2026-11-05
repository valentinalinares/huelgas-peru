"""Extrae cortes de junio de Hojas de Resumen de Planillas, 2002–2007.

Estas observaciones no se anexan silenciosamente a Planilla Electrónica:
son cortes puntuales de junio en empresas privadas de 5 o más trabajadores.
"""
from pathlib import Path
import hashlib
import re
import unicodedata

import pandas as pd
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "planilla_electronica"


def norm(value):
    text = "".join(
        c for c in unicodedata.normalize("NFD", str(value).upper())
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", text).strip()


def source(year):
    files = []
    for path in (ROOT / "anuarios" / str(year)).rglob("*"):
        name = norm(path.name)
        if path.suffix.lower() != ".xls":
            continue
        if not ("PLANILLA" in name or "HOJA DE RESUMEN" in name):
            continue
        if "XII" in name or "CAPITULO 12" in name:
            continue
        files.append(path)
    assert len(files) == 1, (year, files)
    return files[0]


def find_sheet(excel, indicator):
    required = {
        "empleo": ["NUMERO DE TRABAJADORES", "TAMANO DE EMPRESA", "ACTIVIDAD ECONOMICA"],
        "ingreso": ["PROMEDIO DE INGRESO", "TAMANO DE EMPRESA", "ACTIVIDAD ECONOMICA"],
        "negociacion": ["SUJETOS A NEGOCIACION COLECTIVA", "TAMANO DE EMPRESA", "ACTIVIDAD ECONOMICA"],
    }[indicator]
    for sheet in excel.sheet_names:
        data = excel.parse(sheet, header=None)
        header = " ".join(norm(v) for v in data.iloc[:9].values.ravel() if pd.notna(v))
        if "NIVEL NACIONAL" not in header or "LIMA METROPOLITANA" in header:
            continue
        if all(term in header for term in required):
            if indicator == "empleo" and ("PROMEDIO" in header or "NEGOCIACION" in header):
                continue
            return sheet, data
    raise AssertionError((indicator, excel.sheet_names))


def sector(label):
    text = norm(label)
    if "MINAS Y CANTERAS" in text:
        return "mineria"
    if "MANUFACTUR" in text:
        return "manufactura"
    if text == "TOTAL":
        return "total_nacional"
    return None


def table_number(data):
    for value in data.iloc[:5].values.ravel():
        if "CUADRO" in norm(value):
            return re.sub(r"\s+", " ", str(value)).strip()
    return ""


def parse_table(year, path, indicator):
    excel = pd.ExcelFile(path)
    sheet, data = find_sheet(excel, indicator)
    sub_col = total_col = None
    for r in range(min(16, len(data))):
        for c, value in enumerate(data.iloc[r]):
            text = norm(value)
            if "SUB" in text and "TOTAL" in text:
                sub_col = c
            elif text == "TOTAL" and c > 2:
                total_col = c
    assert sub_col is not None and total_col is not None and total_col == sub_col + 3, (year, indicator, sheet)
    rows = []
    for r in range(len(data)):
        label = data.iat[r, 1] if data.shape[1] > 1 else None
        mapped = sector(label)
        if mapped is None:
            continue
        raw_values = [data.iat[r, c] for c in range(sub_col, total_col + 1)]
        values = [0 if norm(v) in {"-", "–", "—"} else pd.to_numeric(v, errors="coerce") for v in raw_values]
        assert not any(pd.isna(v) for v in values), (year, indicator, sheet, r, values)
        rows.append({
            "anio": year,
            "mes_referencia": 6,
            "sector_id": mapped,
            "actividad_economica": re.sub(r"\s+", " ", str(label)).strip(),
            "indicador": indicator,
            "unidad": "soles_corrientes_mensuales" if indicator == "ingreso" else "trabajadores",
            "ejecutivos": values[0],
            "empleados": values[1],
            "obreros": values[2],
            "valor_publicado": values[3],
            "simbolos_cero": ";".join(str(i) for i, v in enumerate(raw_values[:3]) if norm(v) in {"-", "–", "—"}),
            "ambito": "nivel_nacional_sector_privado_empresas_5_mas",
            "periodicidad": "corte_junio",
            "fuente_archivo": str(path.relative_to(ROOT)),
            "fuente_hoja": sheet,
            "fuente_celda": f"{get_column_letter(sub_col+1)}{r+1}:{get_column_letter(total_col+1)}{r+1}",
            "cuadro": table_number(data),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    assert len(rows) == 3, (year, indicator, rows)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, inventory = [], []
    for year in range(2002, 2008):
        path = source(year)
        for indicator in ["empleo", "ingreso", "negociacion"]:
            part = parse_table(year, path, indicator)
            rows.extend(part)
            inventory.append({
                "anio": year,
                "indicador": indicator,
                "fuente_archivo": part[0]["fuente_archivo"],
                "fuente_hoja": part[0]["fuente_hoja"],
                "cuadro": part[0]["cuadro"],
                "periodo": f"junio {year}",
                "ambito": part[0]["ambito"],
                "sha256": part[0]["sha256"],
            })
    base = pd.DataFrame(rows).sort_values(["anio", "indicador", "sector_id"])

    wide = base.pivot(index=["anio", "sector_id"], columns="indicador", values="valor_publicado").reset_index()
    wide = wide.rename(columns={"empleo": "trabajadores", "ingreso": "ingreso_promedio_soles", "negociacion": "trabajadores_sujetos_negociacion"})
    wide["tasa_sujetos_negociacion"] = wide["trabajadores_sujetos_negociacion"] / wide["trabajadores"]
    wide["periodicidad"] = "corte_junio"
    wide["nota_comparabilidad"] = "No equivale a promedio anual ni a Planilla Electronica 2008+."

    controls = []
    for _, row in base.iterrows():
        if row["indicador"] in {"empleo", "negociacion"}:
            calculated = row[["ejecutivos", "empleados", "obreros"]].sum()
            control = "suma_categorias_igual_total"
        else:
            employment = base[
                (base["anio"] == row["anio"]) &
                (base["sector_id"] == row["sector_id"]) &
                (base["indicador"] == "empleo")
            ].iloc[0]
            weights = employment[["ejecutivos", "empleados", "obreros"]].astype(float)
            values = row[["ejecutivos", "empleados", "obreros"]].astype(float)
            calculated = (weights * values).sum() / weights.sum()
            control = "media_ponderada_ingreso_igual_total"
        diff = calculated - row["valor_publicado"]
        if abs(diff) < 1e-8:
            result = "ok"
        elif row["indicador"] == "ingreso" and row["anio"] == 2007:
            result = "ok_con_salvedad_metodologica_2007"
        elif abs(diff) < 0.1:
            result = "ok_redondeo"
        else:
            result = "revisar"
        controls.append({
            "control": control,
            "anio": row["anio"],
            "sector_id": row["sector_id"],
            "indicador": row["indicador"],
            "valor_publicado": row["valor_publicado"],
            "valor_recalculado": calculated,
            "diferencia": diff,
            "resultado": result,
        })
    controls = pd.DataFrame(controls)
    coverage = pd.DataFrame([
        {"indicador": "empleo", "primer_anio": 2002, "ultimo_anio": 2007, "mes_referencia": 6, "sectores": 3, "unidad": "trabajadores", "ruptura": "corte de junio; empresas privadas de 5 o mas"},
        {"indicador": "trabajadores_sujetos_negociacion", "primer_anio": 2002, "ultimo_anio": 2007, "mes_referencia": 6, "sectores": 3, "unidad": "trabajadores", "ruptura": "no equivale a trabajadores sindicalizados"},
        {"indicador": "ingreso_promedio", "primer_anio": 2002, "ultimo_anio": 2007, "mes_referencia": 6, "sectores": 3, "unidad": "soles corrientes mensuales", "ruptura": "ingreso promedio, no remuneracion promedio de Planilla Electronica"},
    ])

    base.to_csv(OUT / "puente_junio_2002_2007.csv", index=False, encoding="utf-8-sig")
    wide.to_csv(OUT / "resumen_puente_junio_2002_2007.csv", index=False, encoding="utf-8-sig")
    controls.to_csv(OUT / "controles_puente_junio_2002_2007.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(inventory).to_csv(OUT / "inventario_puente_junio_2002_2007.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT / "cobertura_puente_junio_2002_2007.csv", index=False, encoding="utf-8-sig")
    print(f"OK: {len(base)} observaciones, {len(wide)} filas comparativas y {len(controls)} controles.")


if __name__ == "__main__":
    main()
