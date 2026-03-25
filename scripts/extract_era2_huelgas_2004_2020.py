from __future__ import annotations

from pathlib import Path

import pandas as pd

from extract_era3_huelgas import (
    ROOT,
    ValidationRow,
    as_number,
    extract_tail_notes,
    fold_text,
    homologate_activity,
    homologate_calificacion,
    homologate_causa,
    homologate_duracion,
    homologate_organizacion,
    homologate_tamano,
    homologate_territorio,
    normalize_text,
    rule_row,
    safe_diff,
)


OUTPUT_DIR = ROOT / "bases" / "era2_homologados_2004_2020"


YEAR_CONFIG = {
    2004: ROOT / "anuarios" / "2004" / "CAPITULO I - HUELGAS 2004.xls",
    2005: ROOT / "anuarios" / "2005" / "CAPITULO I - HUELGAS 2005.xls",
    2006: ROOT / "anuarios" / "2006" / "CAPITULO 1.I - HUELGAS 2006.xls",
    2007: ROOT / "anuarios" / "2007" / "CAPITULO 01.I - HUELGAS 2007.xls",
    2008: ROOT / "anuarios" / "2008" / "ANUARIO 2008" / "CAPITULO 01.I - HUELGAS 2008.xls",
    2009: ROOT / "anuarios" / "2009" / "ANUARIO 2009" / "CAPITULO 01 HUELGAS 2009.xls",
    2010: ROOT / "anuarios" / "2010" / "ANUARIO 2010" / "CAPITULO 01 - HUELGAS 2010.xls",
    2011: ROOT / "anuarios" / "2011" / "ANUARIO 2011" / "CAPITULO 01 - HUELGAS.xls",
    2012: ROOT / "anuarios" / "2012" / "CAPITULO 01 - HUELGAS.xls",
    2013: ROOT / "anuarios" / "2013" / "CAPITULO 01 - HUELGAS.xls",
    2014: ROOT / "anuarios" / "2014" / "I HUELGAS - cuadros" / "v_CAPITULO 01 - HUELGAS.xlsx",
    2015: ROOT / "anuarios" / "2015" / "v_CAPITULO 01 - HUELGAS.xlsx",
    2016: ROOT / "anuarios" / "2016" / "CAPITULO 01 - HUELGAS.xlsx",
    2017: ROOT / "anuarios" / "2017" / "CAPITULO 01 - HUELGAS.xlsx",
    2018: ROOT / "anuarios" / "2018" / "CAPITULO 01 - HUELGAS.xlsx",
    2019: ROOT / "anuarios" / "2019" / "CAPITULO 01 - HUELGAS.xlsx",
    2020: ROOT / "anuarios" / "2020" / "CAPITULO 04 - HUELGAS.xlsx",
}


def find_header_row(df: pd.DataFrame, required: list[str]) -> int:
    for idx in range(min(20, len(df))):
        cells = [normalize_text(value) for value in df.iloc[idx].tolist() if normalize_text(value)]
        row_text = " ".join(cells)
        folded = fold_text(row_text)
        metric_hit_cells = [
            cell
            for cell in cells
            if any(token in fold_text(cell) for token in ["HUELGA", "HUELGAS", "TRABAJ", "HORAS"])
        ]
        if all(token in folded for token in required) and len(metric_hit_cells) >= 3:
            return idx
    raise ValueError(f"No se encontró encabezado con tokens {required}")


def find_specific_header_row(df: pd.DataFrame, category_starts: list[str]) -> int:
    for idx in range(min(20, len(df))):
        cells = [normalize_text(value) for value in df.iloc[idx].tolist() if normalize_text(value)]
        metric_hit_cells = [
            cell
            for cell in cells
            if any(token in fold_text(cell) for token in ["HUELGA", "HUELGAS", "TRABAJ", "HORAS"])
        ]
        category_hit = any(
            fold_text(cell).startswith(token) for token in category_starts for cell in cells
        )
        if category_hit and len(metric_hit_cells) >= 3:
            return idx
    raise ValueError(f"No se encontró encabezado específico para {category_starts}")


def detect_metric_columns(df: pd.DataFrame, header_row: int) -> tuple[int, int, int, int, int | None, int | None, int | None]:
    row = df.iloc[header_row]
    huelgas_col = next(
        idx
        for idx, value in enumerate(row.tolist())
        if fold_text(value) in {"HUELGA", "HUELGAS"}
    )
    trabajadores_col = next(
        idx
        for idx, value in enumerate(row.tolist())
        if fold_text(value).startswith("TRABAJADORES") or fold_text(value).startswith("TRABJADORES")
    )
    horas_col = next(
        idx
        for idx, value in enumerate(row.tolist())
        if fold_text(value).startswith("HORAS") or fold_text(value).startswith("H-H")
    )
    category_col = min(
        idx for idx, value in enumerate(row.tolist()) if normalize_text(value) and idx < huelgas_col
    )
    pct_cols: list[int | None] = []
    for current_col, next_col in zip(
        [huelgas_col, trabajadores_col, horas_col],
        [trabajadores_col, horas_col, len(df.columns) + 1],
    ):
        pct_col = None
        for probe_row in range(header_row, min(header_row + 3, len(df))):
            for idx, value in enumerate(df.iloc[probe_row].tolist()):
                if idx <= current_col or idx >= next_col:
                    continue
                if normalize_text(value) == "%":
                    pct_col = idx
                    break
            if pct_col is not None:
                break
        pct_cols.append(pct_col)
    return category_col, huelgas_col, trabajadores_col, horas_col, pct_cols[0], pct_cols[1], pct_cols[2]


def parse_metric_table(
    df: pd.DataFrame,
    header_tokens: list[str],
    category_starts: list[str] | None = None,
) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = (
        find_specific_header_row(df, category_starts)
        if category_starts
        else find_header_row(df, header_tokens)
    )
    category_col, huelgas_col, trabajadores_col, horas_col, pct_h_col, pct_t_col, pct_hh_col = detect_metric_columns(
        df,
        header_row,
    )
    sample_category_values = [
        normalize_text(df.iloc[idx, category_col]) if category_col < len(df.columns) else ""
        for idx in range(header_row + 1, min(header_row + 6, len(df)))
    ]
    if not any(sample_category_values) and category_col + 1 < len(df.columns):
        shifted_values = [
            normalize_text(df.iloc[idx, category_col + 1])
            for idx in range(header_row + 1, min(header_row + 6, len(df)))
        ]
        if any(shifted_values):
            category_col += 1
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[header_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        alt_category = normalize_text(row.iloc[category_col - 1] if category_col - 1 >= 0 else None)
        if not category:
            category = alt_category
        folded = fold_text(category)
        if folded == "TOTAL":
            totals = {
                "huelgas": as_number(row.iloc[huelgas_col]),
                "trabajadores_comprendidos": as_number(row.iloc[trabajadores_col]),
                "horas_hombre_perdidas": as_number(row.iloc[horas_col]),
            }
            continue
        if any(token in folded for token in ["FUENTE", "ELABORADO", "ELABORACION", "DIRECCION", "OFICINA", "NOTA", "CUADRO", "PERU"]):
            continue
        huelgas = as_number(row.iloc[huelgas_col])
        trabajadores = as_number(row.iloc[trabajadores_col])
        horas = as_number(row.iloc[horas_col])
        if huelgas is None and trabajadores is None and horas is None:
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "pct_huelgas": as_number(row.iloc[pct_h_col]) if pct_h_col is not None else None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": as_number(row.iloc[pct_t_col]) if pct_t_col is not None else None,
                "horas_hombre_perdidas": horas,
                "pct_horas": as_number(row.iloc[pct_hh_col]) if pct_hh_col is not None else None,
            }
        )
    return rows, totals


def parse_activity(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = None
    for idx in range(min(20, len(df))):
        cells = [normalize_text(value) for value in df.iloc[idx].tolist()]
        non_empty = [(col_idx, cell) for col_idx, cell in enumerate(cells) if cell]
        if not non_empty:
            continue
        first_col, first_cell = non_empty[0]
        if first_col > 2:
            continue
        folded_first = fold_text(first_cell)
        if "ACTIVIDAD ECONOM" not in folded_first:
            continue
        if sum(1 for _, cell in non_empty if any(token in fold_text(cell) for token in ["HUELGA", "TRABAJ", "HORAS"])) < 3:
            continue
        header_row = idx
        break
    if header_row is None:
        header_row = find_specific_header_row(df, ["ACTIVIDAD"])

    category_col, huelgas_col, trabajadores_col, horas_col, pct_h_col, pct_t_col, pct_hh_col = detect_metric_columns(
        df,
        header_row,
    )

    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[header_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category:
            continue
        folded = fold_text(category)
        if folded == "TOTAL":
            totals = {
                "huelgas": as_number(row.iloc[huelgas_col]),
                "trabajadores_comprendidos": as_number(row.iloc[trabajadores_col]),
                "horas_hombre_perdidas": as_number(row.iloc[horas_col]),
            }
            continue
        if any(
            token in folded
            for token in ["FUENTE", "ELABORADO", "ELABORACION", "DIRECCION", "OFICINA", "NOTA", "CUADRO", "PERU"]
        ):
            continue
        huelgas = as_number(row.iloc[huelgas_col])
        trabajadores = as_number(row.iloc[trabajadores_col])
        horas = as_number(row.iloc[horas_col])
        if huelgas is None and trabajadores is None and horas is None:
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "pct_huelgas": as_number(row.iloc[pct_h_col]) if pct_h_col is not None else None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": as_number(row.iloc[pct_t_col]) if pct_t_col is not None else None,
                "horas_hombre_perdidas": horas,
                "pct_horas": as_number(row.iloc[pct_hh_col]) if pct_hh_col is not None else None,
            }
        )
    return rows, totals


def parse_calificacion(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = None
    for idx in range(min(20, len(df))):
        cells = [normalize_text(value) for value in df.iloc[idx].tolist() if normalize_text(value)]
        if not cells:
            continue
        first_cell = fold_text(cells[0])
        metric_hit_cells = [
            cell
            for cell in cells
            if any(token in fold_text(cell) for token in ["HUELGA", "HUELGAS", "TRABAJ", "HORAS"])
        ]
        if len(metric_hit_cells) < 3:
            continue
        if "CALIFICACION" in first_cell or "PROCEDENCIA" in first_cell:
            header_row = idx
            break
    if header_row is None:
        try:
            header_row = find_specific_header_row(df, ["CALIFICACION"])
        except ValueError:
            header_row = find_specific_header_row(df, ["PROCEDENCIA"])
    row = df.iloc[header_row]
    huelgas_col = next(idx for idx, value in enumerate(row.tolist()) if "HUELGAS" in fold_text(value))
    trabajadores_col = next(
        idx
        for idx, value in enumerate(row.tolist())
        if "TRABAJADORES" in fold_text(value) or "COMPRENDIDOS" in fold_text(value)
    )
    horas_col = next(
        idx
        for idx, value in enumerate(row.tolist())
        if "HORAS" in fold_text(value) or "H-H" in fold_text(value)
    )
    category_col = min(
        idx for idx, value in enumerate(row.tolist()) if normalize_text(value) and idx < huelgas_col
    )
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[header_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category:
            continue
        folded = fold_text(category)
        if folded == "TOTAL":
            totals = {
                "huelgas": as_number(row.iloc[huelgas_col]),
                "trabajadores_comprendidos": as_number(row.iloc[trabajadores_col]),
                "horas_hombre_perdidas": as_number(row.iloc[horas_col]),
            }
            continue
        if any(token in folded for token in ["FUENTE", "ELABORADO", "ELABORACION", "DIRECCION", "CUADRO", "PERU"]):
            continue
        if not any(
            token in folded
            for token in [
                "CONFORME",
                "CONFORMIDAD",
                "PROCEDENTE",
                "PROCEDENCIA",
                "IMPROCEDENTE",
                "ILEGALIDAD",
                "CON AUTO DE ILEGALIDAD",
            ]
        ):
            continue
        huelgas = as_number(row.iloc[huelgas_col])
        trabajadores = as_number(row.iloc[trabajadores_col])
        horas = as_number(row.iloc[horas_col])
        if huelgas is None and trabajadores is None and horas is None:
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "pct_huelgas": None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": None,
                "horas_hombre_perdidas": horas,
                "pct_horas": None,
            }
        )
    return rows, totals


def parse_causas(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    total_idx = None
    for idx, row in df.iterrows():
        f0 = fold_text(row.iloc[0] if len(row) > 0 else None)
        f1 = fold_text(row.iloc[1] if len(row) > 1 else None)
        if f0 == "TOTAL" or f1 == "TOTAL":
            total_idx = idx
            break
    if total_idx is None:
        raise ValueError("No se encontró TOTAL en causas")
    row = df.iloc[total_idx]
    width = len(df.columns)
    if width == 19:
        rows = [
            {
                "categoria_original": "PLIEGO RECLAMOS",
                "huelgas": as_number(row.iloc[1]),
                "pct_huelgas": as_number(row.iloc[2]),
                "trabajadores_comprendidos": as_number(row.iloc[7]),
                "pct_trabajadores": as_number(row.iloc[8]),
                "horas_hombre_perdidas": as_number(row.iloc[13]),
                "pct_horas": as_number(row.iloc[14]),
            },
            {
                "categoria_original": "OTRAS CAUSAS",
                "huelgas": as_number(row.iloc[3]),
                "pct_huelgas": as_number(row.iloc[4]),
                "trabajadores_comprendidos": as_number(row.iloc[9]),
                "pct_trabajadores": as_number(row.iloc[10]),
                "horas_hombre_perdidas": as_number(row.iloc[15]),
                "pct_horas": as_number(row.iloc[16]),
            },
        ]
        totals = {
            "huelgas": as_number(row.iloc[5]),
            "trabajadores_comprendidos": as_number(row.iloc[11]),
            "horas_hombre_perdidas": as_number(row.iloc[17]),
        }
        return rows, totals
    if width == 20:
        rows = [
            {
                "categoria_original": "PLIEGO RECLAMOS",
                "huelgas": as_number(row.iloc[2]),
                "pct_huelgas": as_number(row.iloc[3]),
                "trabajadores_comprendidos": as_number(row.iloc[8]),
                "pct_trabajadores": as_number(row.iloc[9]),
                "horas_hombre_perdidas": as_number(row.iloc[14]),
                "pct_horas": as_number(row.iloc[15]),
            },
            {
                "categoria_original": "OTRAS CAUSAS",
                "huelgas": as_number(row.iloc[4]),
                "pct_huelgas": as_number(row.iloc[5]),
                "trabajadores_comprendidos": as_number(row.iloc[10]),
                "pct_trabajadores": as_number(row.iloc[11]),
                "horas_hombre_perdidas": as_number(row.iloc[16]),
                "pct_horas": as_number(row.iloc[17]),
            },
        ]
        totals = {
            "huelgas": as_number(row.iloc[6]),
            "trabajadores_comprendidos": as_number(row.iloc[12]),
            "horas_hombre_perdidas": as_number(row.iloc[18]),
        }
        return rows, totals
    if width == 21:
        rows = [
            {
                "categoria_original": "PLIEGO RECLAMOS",
                "huelgas": as_number(row.iloc[2]),
                "pct_huelgas": as_number(row.iloc[3]),
                "trabajadores_comprendidos": as_number(row.iloc[8]),
                "pct_trabajadores": as_number(row.iloc[9]),
                "horas_hombre_perdidas": as_number(row.iloc[14]),
                "pct_horas": as_number(row.iloc[16]),
            },
            {
                "categoria_original": "OTRAS CAUSAS",
                "huelgas": as_number(row.iloc[4]),
                "pct_huelgas": as_number(row.iloc[5]),
                "trabajadores_comprendidos": as_number(row.iloc[10]),
                "pct_trabajadores": as_number(row.iloc[11]),
                "horas_hombre_perdidas": as_number(row.iloc[17]),
                "pct_horas": as_number(row.iloc[18]),
            },
        ]
        totals = {
            "huelgas": as_number(row.iloc[6]),
            "trabajadores_comprendidos": as_number(row.iloc[12]),
            "horas_hombre_perdidas": as_number(row.iloc[19]),
        }
        return rows, totals
    if width == 22:
        rows = [
            {
                "categoria_original": "PLIEGO RECLAMOS",
                "huelgas": as_number(row.iloc[2]),
                "pct_huelgas": as_number(row.iloc[3]),
                "trabajadores_comprendidos": as_number(row.iloc[8]),
                "pct_trabajadores": as_number(row.iloc[10]),
                "horas_hombre_perdidas": as_number(row.iloc[15]),
                "pct_horas": as_number(row.iloc[17]),
            },
            {
                "categoria_original": "OTRAS CAUSAS",
                "huelgas": as_number(row.iloc[4]),
                "pct_huelgas": as_number(row.iloc[5]),
                "trabajadores_comprendidos": as_number(row.iloc[11]),
                "pct_trabajadores": as_number(row.iloc[12]),
                "horas_hombre_perdidas": as_number(row.iloc[18]),
                "pct_horas": as_number(row.iloc[19]),
            },
        ]
        totals = {
            "huelgas": as_number(row.iloc[6]),
            "trabajadores_comprendidos": as_number(row.iloc[13]),
            "horas_hombre_perdidas": as_number(row.iloc[20]),
        }
        return rows, totals
    if width >= 35:
        rows = [
            {
                "categoria_original": "PLIEGO RECLAMOS",
                "huelgas": as_number(row.iloc[2]),
                "pct_huelgas": as_number(row.iloc[4]),
                "trabajadores_comprendidos": as_number(row.iloc[14]),
                "pct_trabajadores": as_number(row.iloc[16]),
                "horas_hombre_perdidas": as_number(row.iloc[26]),
                "pct_horas": as_number(row.iloc[28]),
            },
            {
                "categoria_original": "OTRAS CAUSAS",
                "huelgas": as_number(row.iloc[6]),
                "pct_huelgas": as_number(row.iloc[8]),
                "trabajadores_comprendidos": as_number(row.iloc[18]),
                "pct_trabajadores": as_number(row.iloc[20]),
                "horas_hombre_perdidas": as_number(row.iloc[30]),
                "pct_horas": as_number(row.iloc[32]),
            },
        ]
        totals = {
            "huelgas": as_number(row.iloc[10]),
            "trabajadores_comprendidos": as_number(row.iloc[22]),
            "horas_hombre_perdidas": as_number(row.iloc[34]),
        }
        return rows, totals
    rows = [
        {
            "categoria_original": "PLIEGO RECLAMOS",
            "huelgas": as_number(row.iloc[2]),
            "pct_huelgas": as_number(row.iloc[3]),
            "trabajadores_comprendidos": as_number(row.iloc[8]),
            "pct_trabajadores": as_number(row.iloc[10]),
            "horas_hombre_perdidas": as_number(row.iloc[15]),
            "pct_horas": as_number(row.iloc[17]),
        },
        {
            "categoria_original": "OTRAS CAUSAS",
            "huelgas": as_number(row.iloc[4]),
            "pct_huelgas": as_number(row.iloc[5]),
            "trabajadores_comprendidos": as_number(row.iloc[11]),
            "pct_trabajadores": as_number(row.iloc[12]),
            "horas_hombre_perdidas": as_number(row.iloc[18]),
            "pct_horas": as_number(row.iloc[20]),
        },
    ]
    totals = {
        "huelgas": as_number(row.iloc[6]),
        "trabajadores_comprendidos": as_number(row.iloc[13]),
        "horas_hombre_perdidas": as_number(row.iloc[21]),
    }
    return rows, totals


def validate_module(
    anio: int,
    modulo: str,
    hoja_excel: str,
    df: pd.DataFrame,
    totals: dict[str, float | None],
) -> list[ValidationRow]:
    validations: list[ValidationRow] = []
    if modulo == "territorio":
        for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
            source_value = totals.get(metric)
            overall = pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)
            overall_value = None if pd.isna(overall) else float(overall)
            validations.append(
                ValidationRow(
                    anio=anio,
                    modulo=modulo,
                    hoja_excel=hoja_excel,
                    metrica=f"{metric}_todos_los_niveles",
                    total_extraido=overall_value,
                    total_fuente=source_value,
                    diferencia=safe_diff(overall_value, source_value),
                    estado="estructura_mixta",
                )
            )
        return validations
    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        extracted = pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)
        extracted_value = None if pd.isna(extracted) else float(extracted)
        source_value = totals.get(metric)
        diff = safe_diff(extracted_value, source_value)
        state = "ok" if diff is not None and abs(diff) <= 0.01 else "revisar"
        validations.append(
            ValidationRow(
                anio=anio,
                modulo=modulo,
                hoja_excel=hoja_excel,
                metrica=metric,
                total_extraido=extracted_value,
                total_fuente=source_value,
                diferencia=diff,
                estado=state,
            )
        )
    return validations


def build_module_frame(anio: int, modulo: str, hoja_excel: str, df_raw: pd.DataFrame):
    notes = extract_tail_notes(df_raw)
    rules: list[dict[str, object]] = []
    if modulo == "actividad":
        rows, totals = parse_activity(df_raw)
    elif modulo == "territorio":
        rows, totals = parse_metric_table(
            df_raw,
            ["TRABAJ", "HORAS"],
            category_starts=["DIRECCIONES", "DIRECCION", "REGIONES"],
        )
    elif modulo == "causas":
        rows, totals = parse_causas(df_raw)
    elif modulo == "calificacion":
        rows, totals = parse_calificacion(df_raw)
    elif modulo == "organizacion":
        rows, totals = parse_metric_table(
            df_raw,
            ["ORGANIZ", "HUELGAS", "TRABAJADORES", "HORAS"],
            category_starts=["ORGANIZACION", "ORGANIZACIÓN"],
        )
    elif modulo == "tamano":
        rows, totals = parse_metric_table(
            df_raw,
            ["TRABAJADORES", "HUELGAS", "HORAS"],
            category_starts=["NUMERO", "NÚMERO"],
        )
    elif modulo == "duracion":
        rows, totals = parse_metric_table(
            df_raw,
            ["HUELGAS", "TRABAJADORES", "HORAS"],
            category_starts=["DURACION", "DURACIÓN", "DIAS", "DÍAS"],
        )
    else:
        raise ValueError(modulo)

    current_region_slug = None
    output_rows: list[dict[str, object]] = []
    for row in rows:
        original = normalize_text(row["categoria_original"])
        nivel = None
        parent = None
        if modulo == "actividad":
            fina, agregada, regla = homologate_activity(original)
        elif modulo == "calificacion":
            fina, agregada, regla = homologate_calificacion(original)
        elif modulo == "organizacion":
            fina, agregada, regla = homologate_organizacion(original)
        elif modulo == "tamano":
            fina, agregada, regla = homologate_tamano(original)
        elif modulo == "duracion":
            fina, agregada, regla = homologate_duracion(original)
        elif modulo == "causas":
            fina, agregada, regla = homologate_causa(original)
        else:
            fina, agregada, nivel, parent, regla = homologate_territorio(original, current_region_slug)
            if nivel == "regional":
                current_region_slug = fina
        rules.append(rule_row(anio, modulo, original, fina, agregada, regla))
        output_rows.append(
            {
                "anio": anio,
                "modulo": modulo,
                "hoja_excel": hoja_excel,
                "categoria_original": original,
                "categoria_homologada_fina": fina,
                "categoria_homologada_agregada": agregada,
                "regla_homologacion": regla,
                "nivel_territorial": nivel,
                "territorio_padre": parent,
                "huelgas": row.get("huelgas"),
                "pct_huelgas": row.get("pct_huelgas"),
                "trabajadores_comprendidos": row.get("trabajadores_comprendidos"),
                "pct_trabajadores": row.get("pct_trabajadores"),
                "horas_hombre_perdidas": row.get("horas_hombre_perdidas"),
                "pct_horas": row.get("pct_horas"),
                "flag_hhp_arrastre": int(any("HORAS - HOMBRE PERDIDAS GENERADAS" in fold_text(note) for note in notes)),
                "flag_faltante_fuente": int(any("NO SE DISPONE" in fold_text(note) for note in notes)),
                "flag_paro_nacional_registrado_lima": int(
                    modulo == "territorio" and (original.endswith("*") or "LIMA METROPOLITANA" in fold_text(original))
                ),
                "nota_fuente": " | ".join(notes),
            }
        )
    module_df = pd.DataFrame(output_rows)
    rules_df = pd.DataFrame(rules).drop_duplicates()
    validations = validate_module(anio, modulo, hoja_excel, module_df, totals)
    return module_df, rules_df, validations, notes


def process_year(anio: int, path: Path) -> None:
    module_frames: dict[str, pd.DataFrame] = {}
    rules_frames: list[pd.DataFrame] = []
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []
    for modulo, hoja in {
        "actividad": "C-3",
        "territorio": "C-5",
        "causas": "C-6",
        "calificacion": "C-7",
        "organizacion": "C-8",
        "tamano": "C-9",
        "duracion": "C-10",
    }.items():
        df_raw = pd.read_excel(path, sheet_name=hoja, header=None)
        module_df, rules_df, validations, notes = build_module_frame(anio, modulo, hoja, df_raw)
        module_frames[modulo] = module_df
        rules_frames.append(rules_df)
        validation_rows.extend(validations)
        for note in notes:
            notes_rows.append({"anio": anio, "modulo": modulo, "hoja_excel": hoja, "nota_fuente": note})

    excel_path = OUTPUT_DIR / f"huelgas_{anio}_homologado.xlsx"
    summary_df = pd.DataFrame(
        [
            {
                "anio": anio,
                "archivo_fuente": str(path.relative_to(ROOT)),
                "archivo_salida": str(excel_path.relative_to(ROOT)),
                "modulos_generados": len(module_frames),
                "filas_totales": sum(len(df) for df in module_frames.values()),
                "validaciones_revisar": int(
                    pd.DataFrame([row.__dict__ for row in validation_rows])["estado"].eq("revisar").sum()
                ),
                "notas_fuente": len(notes_rows),
            }
        ]
    )
    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    dictionary_df = pd.concat(rules_frames, ignore_index=True).drop_duplicates()
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen", index=False)
        for modulo, frame in module_frames.items():
            frame.to_excel(writer, sheet_name=modulo, index=False)
        dictionary_df.to_excel(writer, sheet_name="diccionario_aplicado", index=False)
        notes_df.to_excel(writer, sheet_name="observaciones_fuente", index=False)
        validation_df.to_excel(writer, sheet_name="validacion", index=False)
    print(f"[ok] {anio} -> {excel_path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for anio, path in YEAR_CONFIG.items():
        process_year(anio, path)


if __name__ == "__main__":
    main()
