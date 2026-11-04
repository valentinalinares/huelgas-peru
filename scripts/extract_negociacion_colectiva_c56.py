"""Construye la base histórica del cuadro C-56 del Anuario MTPE 2025.

Salidas:
  1. Base larga con todas las actividades económicas y el total nacional.
  2. Serie comparativa prioritaria: minería, manufactura y total nacional.
  3. Auditoría de los años 1995-2024 contra el Anuario MTPE 2024.

El archivo fuente usa dos bloques de años y contiene celdas de formato muy por
debajo del cuadro. Por eso la extracción identifica los años de cada encabezado
y usa una tabla explícita de filas/etiquetas, evitando depender del rango usado
de Excel o de los caracteres dañados que aparecen en algunos rótulos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_2025 = (
    PROJECT_ROOT
    / "anuarios"
    / "2025"
    / "CAP 02 - NEGOCIACIONES COLECTIVAS_2025_v2-MEE.xlsx"
)
SOURCE_2024 = (
    PROJECT_ROOT
    / "anuarios"
    / "2024"
    / "CAP 02 - NEGOCIACIONES COLECTIVAS_2024.xlsx"
)
OUTPUT_DIR = PROJECT_ROOT / "bases" / "negociacion_colectiva"

SHEET_NAME = "C-56"
SOURCE_INSTITUTION = "Ministerio de Trabajo y Promoción del Empleo (MTPE)"

# Posición y etiqueta normalizada de las 15 actividades publicadas por el MTPE.
SECTORS = [
    (0, "agricultura_ganaderia_caza_silvicultura", "Agricultura, ganadería, caza y silvicultura"),
    (1, "pesca", "Pesca"),
    (2, "minas_canteras", "Explotación de minas y canteras"),
    (3, "industrias_manufactureras", "Industrias manufactureras"),
    (4, "electricidad_gas_agua", "Suministro de electricidad, gas y agua"),
    (5, "construccion", "Construcción"),
    (6, "comercio_reparacion_vehiculos", "Comercio al por mayor y menor; reparación de vehículos automotores"),
    (7, "hoteles_restaurantes", "Hoteles y restaurantes"),
    (8, "transporte_almacenamiento_comunicaciones", "Transporte, almacenamiento y comunicaciones"),
    (9, "intermediacion_financiera", "Intermediación financiera"),
    (10, "actividades_inmobiliarias_empresariales_alquiler", "Actividades inmobiliarias, empresariales y de alquiler"),
    (11, "administracion_publica_defensa", "Administración pública y defensa"),
    (12, "ensenanza", "Enseñanza"),
    (13, "servicios_sociales_salud", "Servicios sociales y de salud"),
    (14, "otros_servicios_comunitarios_sociales_personales", "Otras actividades de servicios comunitarios, sociales y personales"),
]

# (fila de años, primera fila de actividad, fila del total), índices base cero.
BLOCKS = [(5, 6, 22), (25, 26, 42)]


def year_columns(frame: pd.DataFrame, header_row: int) -> list[tuple[int, int]]:
    """Devuelve pares (columna, año) para un encabezado del cuadro."""
    result: list[tuple[int, int]] = []
    for column, value in enumerate(frame.iloc[header_row]):
        if pd.notna(value) and isinstance(value, (int, float)):
            year = int(value)
            if 1990 <= year <= 2030:
                result.append((column, year))
    return result


def analytic_group(sector_id: str) -> str:
    if sector_id == "minas_canteras":
        return "mineria"
    if sector_id == "industrias_manufactureras":
        return "manufactura"
    if sector_id == "total_nacional":
        return "total_nacional"
    return "otras_actividades"


def comparability_note(year: int, sector_id: str) -> str:
    notes: list[str] = []
    if year == 2025:
        notes.append(
            "El MTPE indica que 2025 incluye convenios solucionados en 2019-2024 "
            "cuya vigencia comprende 2025."
        )
    if sector_id == "minas_canteras":
        notes.append(
            "La categoría Explotación de minas y canteras no equivale exactamente "
            "a minería metálica; contratistas mineros pueden figurar en otras actividades."
        )
    return " ".join(notes)


def extract_table(path: Path, source_year: int) -> pd.DataFrame:
    frame = pd.read_excel(path, sheet_name=SHEET_NAME, header=None, dtype=object)
    records: list[dict[str, object]] = []

    for header_row, first_sector_row, total_row in BLOCKS:
        columns = year_columns(frame, header_row)
        for offset, sector_id, normalized_label in SECTORS:
            row = first_sector_row + offset
            source_label = frame.iat[row, 2]
            for column, year in columns:
                records.append(
                    {
                        "anio": year,
                        "sector_id": sector_id,
                        "actividad_economica": normalized_label,
                        "actividad_original_mtpe": str(source_label),
                        "grupo_analitico": analytic_group(sector_id),
                        "convenios_colectivos": int(frame.iat[row, column]),
                        "unidad": "número de convenios colectivos",
                        "fuente_institucion": SOURCE_INSTITUTION,
                        "fuente_documento": path.name,
                        "fuente_anio": source_year,
                        "hoja": SHEET_NAME,
                        "cuadro": "C-56",
                        "nota_comparabilidad": comparability_note(year, sector_id),
                    }
                )

        for column, year in columns:
            sector_id = "total_nacional"
            records.append(
                {
                    "anio": year,
                    "sector_id": sector_id,
                    "actividad_economica": "Total nacional",
                    "actividad_original_mtpe": "TOTAL",
                    "grupo_analitico": analytic_group(sector_id),
                    "convenios_colectivos": int(frame.iat[total_row, column]),
                    "unidad": "número de convenios colectivos",
                    "fuente_institucion": SOURCE_INSTITUTION,
                    "fuente_documento": path.name,
                    "fuente_anio": source_year,
                    "hoja": SHEET_NAME,
                    "cuadro": "C-56",
                    "nota_comparabilidad": comparability_note(year, sector_id),
                }
            )

    return pd.DataFrame.from_records(records).sort_values(["anio", "sector_id"]).reset_index(drop=True)


def validate_master(master: pd.DataFrame) -> dict[str, object]:
    expected_years = list(range(1995, 2026))
    assert sorted(master["anio"].unique().tolist()) == expected_years
    assert master["sector_id"].nunique() == 16
    assert len(master) == 31 * 16
    assert not master.duplicated(["anio", "sector_id"]).any()
    assert master["convenios_colectivos"].notna().all()
    assert (master["convenios_colectivos"] >= 0).all()

    sector_sums = (
        master.loc[master["sector_id"] != "total_nacional"]
        .groupby("anio", as_index=True)["convenios_colectivos"]
        .sum()
    )
    totals = (
        master.loc[master["sector_id"] == "total_nacional"]
        .set_index("anio")["convenios_colectivos"]
    )
    reconciliation = sector_sums.sub(totals)
    assert (reconciliation == 0).all()

    return {
        "periodo": "1995-2025",
        "filas_base_larga": int(len(master)),
        "anios": int(master["anio"].nunique()),
        "actividades_mas_total": int(master["sector_id"].nunique()),
        "anios_que_cuadran_con_total_publicado": int((reconciliation == 0).sum()),
    }


def build_priority_series(master: pd.DataFrame) -> pd.DataFrame:
    priority = master.loc[
        master["sector_id"].isin(
            ["minas_canteras", "industrias_manufactureras", "total_nacional"]
        ),
        ["anio", "sector_id", "convenios_colectivos"],
    ]
    wide = (
        priority.pivot(index="anio", columns="sector_id", values="convenios_colectivos")
        .reset_index()
        .rename(
            columns={
                "minas_canteras": "mineria_minas_y_canteras",
                "industrias_manufactureras": "manufactura",
                "total_nacional": "total_nacional",
            }
        )
    )
    wide["participacion_mineria_en_total_pct"] = (
        100 * wide["mineria_minas_y_canteras"] / wide["total_nacional"]
    ).round(2)
    wide["participacion_manufactura_en_total_pct"] = (
        100 * wide["manufactura"] / wide["total_nacional"]
    ).round(2)
    return wide


def compare_sources(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    columns = ["anio", "sector_id", "actividad_economica", "convenios_colectivos"]
    comparison = old[columns].merge(
        new[columns],
        on=["anio", "sector_id", "actividad_economica"],
        how="inner",
        suffixes=("_anuario_2024", "_anuario_2025"),
        validate="one_to_one",
    )
    comparison["diferencia"] = (
        comparison["convenios_colectivos_anuario_2025"]
        - comparison["convenios_colectivos_anuario_2024"]
    )
    comparison["resultado_validacion"] = comparison["diferencia"].map(
        lambda value: "sin cambio" if value == 0 else "revisado"
    )
    return comparison.sort_values(["anio", "sector_id"]).reset_index(drop=True)


def main() -> None:
    if not SOURCE_2025.exists() or not SOURCE_2024.exists():
        missing = [str(path) for path in (SOURCE_2025, SOURCE_2024) if not path.exists()]
        raise FileNotFoundError("Faltan fuentes: " + "; ".join(missing))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    master = extract_table(SOURCE_2025, 2025)
    old = extract_table(SOURCE_2024, 2024)
    summary = validate_master(master)
    priority = build_priority_series(master)
    validation = compare_sources(old, master)

    assert len(validation) == 30 * 16
    assert (validation["diferencia"] == 0).all()

    master_path = OUTPUT_DIR / "base_negociacion_colectiva_c56_1995_2025.csv"
    priority_path = OUTPUT_DIR / "serie_mineria_manufactura_total_1995_2025.csv"
    validation_path = OUTPUT_DIR / "validacion_c56_2024_vs_2025.csv"

    master.to_csv(master_path, index=False, encoding="utf-8-sig")
    priority.to_csv(priority_path, index=False, encoding="utf-8-sig")
    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")

    values_2025 = priority.loc[priority["anio"] == 2025].iloc[0]
    summary.update(
        {
            "celdas_historicas_comparadas_2024_vs_2025": int(len(validation)),
            "celdas_historicas_revisadas": int((validation["diferencia"] != 0).sum()),
            "valor_2025_mineria_minas_y_canteras": int(values_2025["mineria_minas_y_canteras"]),
            "valor_2025_manufactura": int(values_2025["manufactura"]),
            "valor_2025_total_nacional": int(values_2025["total_nacional"]),
            "fuente_maestra": str(SOURCE_2025.relative_to(PROJECT_ROOT)),
            "fuente_control": str(SOURCE_2024.relative_to(PROJECT_ROOT)),
        }
    )
    (OUTPUT_DIR / "resumen_validacion.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\nSalidas:")
    for path in (master_path, priority_path, validation_path):
        print(path)


if __name__ == "__main__":
    main()
