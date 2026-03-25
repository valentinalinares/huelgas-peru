from __future__ import annotations

from pathlib import Path

import pandas as pd

from extract_era3_huelgas import (
    ROOT,
    ValidationRow,
    as_number,
    extract_tail_notes,
    fold_text,
    homologate_calificacion,
    homologate_causa,
    homologate_tamano,
    normalize_text,
    rule_row,
    safe_diff,
    slug_text,
)


OUTPUT_DIR = ROOT / "bases" / "era2_homologados_1996_1999"
MODULE_ORDER = [
    "actividad",
    "territorio",
    "causas",
    "calificacion",
    "organizacion",
    "tamano",
    "duracion",
]
MODULE_COLUMNS = [
    "anio",
    "modulo",
    "hoja_excel",
    "categoria_original",
    "categoria_homologada_fina",
    "categoria_homologada_agregada",
    "regla_homologacion",
    "nivel_territorial",
    "territorio_padre",
    "huelgas",
    "pct_huelgas",
    "trabajadores_comprendidos",
    "pct_trabajadores",
    "horas_hombre_perdidas",
    "pct_horas",
    "flag_hhp_arrastre",
    "flag_faltante_fuente",
    "flag_paro_nacional_registrado_lima",
    "nota_fuente",
]


YEAR_CONFIG: dict[int, dict[str, object]] = {
    1996: {
        "path": ROOT / "anuarios" / "1996" / "I-HUEL~1.XLS",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-7",
            "calificacion": "C-11",
            "organizacion": "C-12",
            "tamano": "C-13",
            "duracion": "C-14",
        },
    },
    1997: {
        "path": ROOT / "anuarios" / "1997" / "I-HUELGA.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-7",
            "calificacion": "C-8",
            "organizacion": "C-9",
            "tamano": "C-10",
            "duracion": "C-11",
        },
    },
    1998: {
        "path": ROOT / "anuarios" / "1998" / "I-HUEL98.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-9",
            "duracion": "C-10",
        },
    },
    1999: {
        "path": ROOT / "anuarios" / "1999" / "I-HUEL99.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-10",
            "duracion": "C-9",
        },
    },
}


YEAR_NOTES = {
    1996: {
        "actividad": "1996: actividad leida desde C-3 con parser especifico del layout antiguo; se ignoran encabezados y porcentajes.",
        "territorio": "1996: territorio leido desde C-5; se preserva geografia historica y se marca estructura mixta region/ciudad.",
        "causas": "1996: causas leidas desde C-7 anual; no se usa la tabla mensual C-6.",
        "calificacion": "1996: calificacion leida desde C-11.",
        "organizacion": "1996: organizacion leida desde C-12; se toman solo las columnas 1996 de la serie 1995-1996.",
        "tamano": "1996: tamano leido desde C-13 con columnas fijas del layout antiguo.",
        "duracion": "1996: duracion leida desde C-14; se agregan los tramos largos viejos en 16_mas_dias.",
    },
    1997: {
        "actividad": "1997: actividad leida desde C-3 con parser especifico del layout antiguo; se ignoran encabezados y porcentajes.",
        "territorio": "1997: territorio leido desde C-5; se preserva geografia historica y se marca estructura mixta region/zona.",
        "causas": "1997: causas leidas desde C-7 anual; no se usa la tabla mensual C-6.",
        "calificacion": "1997: calificacion leida desde C-8.",
        "organizacion": "1997: organizacion leida desde C-9; se toman solo las columnas 1997 de la serie 1996-1997.",
        "tamano": "1997: tamano leido desde C-10 con columnas fijas del layout antiguo.",
        "duracion": "1997: duracion leida desde C-11; se agregan los tramos largos viejos en 16_mas_dias.",
    },
    1998: {
        "actividad": "1998: actividad leida desde C-3 con parser especifico del layout antiguo; se ignoran encabezados y porcentajes.",
        "territorio": "1998: territorio leido desde C-5; se preserva geografia historica y se marca estructura mixta region/zona.",
        "causas": "1998: causas leidas desde la fila TOTAL de C-6.",
        "calificacion": "1998: calificacion leida desde C-7.",
        "organizacion": "1998: organizacion leida desde C-8 con parser del cuadro anual simple.",
        "tamano": "1998: tamano leido desde C-9 con columnas fijas del layout antiguo.",
        "duracion": "1998: duracion leida desde C-10; se agregan los tramos largos viejos en 16_mas_dias.",
    },
    1999: {
        "actividad": "1999: actividad leida desde C-3 con parser especifico del layout antiguo; se ignoran encabezados, ranking lateral y porcentajes.",
        "territorio": "1999: territorio leido desde C-5; se marca estructura mixta y el doble registro regional/zona del cuadro.",
        "causas": "1999: causas leidas desde la fila TOTAL de C-6.",
        "calificacion": "1999: calificacion leida desde C-7.",
        "organizacion": "1999: organizacion leida desde C-8 con parser del cuadro anual simple antiguo.",
        "tamano": "1999: tamano leido desde C-10 con columnas fijas del layout antiguo.",
        "duracion": "1999: duracion leida desde C-9; se agregan los tramos largos viejos en 16_mas_dias.",
    },
}


TERRITORY_HEADERS_OLD = {
    1996: {
        "AREQUIPA",
        "ANDRES A. CACERES",
        "CHAVIN",
        "GRAU",
        "INKA",
        "LA LIBERTAD",
        "LIBERTADORES WARI",
        "LIMA",
        "LORETO",
        "MOQUEGUA - TACNA - PUNO",
        "NOR - ORIENTAL DEL MARAÑON",
    },
    1997: {
        "AREQUIPA",
        "ANDRES A. CACERES",
        "CHAVIN",
        "GRAU",
        "INKA",
        "LA LIBERTAD",
        "LIBERTADORES WARI",
        "LIMA",
        "LORETO",
        "MOQUEGUA - TACNA - PUNO",
        "UCAYALI",
    },
    1998: {
        "AREQUIPA",
        "ANDRES A. CACERES",
        "CHAVIN",
        "GRAU",
        "INKA",
        "LA LIBERTAD",
        "LIBERTADORES WARI",
        "LIMA",
        "LORETO",
        "MOQUEGUA - TACNA - PUNO",
        "NOR ORIENTAL DEL MARAÑON",
        "SAN MARTIN",
    },
}

TERRITORY_HEADERS_1999 = {
    "ANCASH",
    "AREQUIPA",
    "CAJAMARCA",
    "CUSCO",
    "ICA",
    "JUNIN",
    "LA LIBERTAD",
    "LAMBAYEQUE",
    "LIMA",
    "LORETO",
    "MOQUEGUA",
    "PASCO",
    "PIURA",
    "PUNO",
    "TACNA",
    "UCAYALI",
}


def is_total_label(value: object) -> bool:
    return fold_text(value).replace(" ", "") == "TOTAL"


def year_matches(value: object, year: int) -> bool:
    text = normalize_text(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text in {str(year), str(year)[-2:]}


def validate_module(
    anio: int,
    modulo: str,
    hoja_excel: str,
    df: pd.DataFrame,
    totals: dict[str, float | None],
) -> list[ValidationRow]:
    if modulo == "territorio":
        rows: list[ValidationRow] = []
        for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
            extracted = pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)
            extracted_value = None if pd.isna(extracted) else float(extracted)
            source_value = totals.get(metric)
            rows.append(
                ValidationRow(
                    anio=anio,
                    modulo=modulo,
                    hoja_excel=hoja_excel,
                    metrica=f"{metric}_todos_los_niveles",
                    total_extraido=extracted_value,
                    total_fuente=source_value,
                    diferencia=safe_diff(extracted_value, source_value),
                    estado="estructura_mixta",
                )
            )
        return rows

    validations: list[ValidationRow] = []
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


def find_row_with_token(df: pd.DataFrame, token: str, preferred_col: int | None = None) -> int:
    folded_token = fold_text(token)
    for idx in range(min(25, len(df))):
        row = df.iloc[idx].tolist()
        if preferred_col is not None and preferred_col < len(row):
            if folded_token in fold_text(row[preferred_col]):
                return idx
        joined = " ".join(normalize_text(value) for value in row if normalize_text(value))
        if folded_token in fold_text(joined):
            return idx
    raise ValueError(f"No se encontro fila con token {token}")


def parse_fixed_table(
    df: pd.DataFrame,
    start_row: int,
    category_col: int,
    huelgas_col: int,
    trabajadores_col: int,
    horas_col: int,
    pct_h_col: int | None = None,
    pct_t_col: int | None = None,
    pct_hh_col: int | None = None,
) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[start_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        total_label = None
        for probe_col in {0, category_col}:
            if probe_col < len(row):
                probe_value = normalize_text(row.iloc[probe_col])
                if is_total_label(probe_value):
                    total_label = probe_value
                    break
        if not category and not total_label:
            continue
        category_for_checks = category or total_label or ""
        folded = fold_text(category_for_checks)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "CUADRO", "PAG."]):
            continue
        huelgas = as_number(row.iloc[huelgas_col] if huelgas_col < len(row) else None)
        trabajadores = as_number(row.iloc[trabajadores_col] if trabajadores_col < len(row) else None)
        horas = as_number(row.iloc[horas_col] if horas_col < len(row) else None)
        if total_label:
            totals = {
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
            continue
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


def parse_activity_old(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_row = next(
        idx
        for idx in range(min(25, len(df)))
        if fold_text(df.iloc[idx, 0]).startswith("ACTIVIDAD")
        and "HUELGAS" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
    )
    return parse_fixed_table(df, start_row, 0, 1, 5, 9, 3, 7, 11)


def parse_causas_9697(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_row = next(
        idx
        for idx in range(min(25, len(df)))
        if fold_text(df.iloc[idx, 0]).startswith("CAUSAS")
        and "HUELGAS" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
    )
    return parse_fixed_table(df, start_row, 0, 1, 4, 7, 2, 5, 8)


def parse_causas_9899(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    total_idx = None
    for idx, row in df.iterrows():
        f0 = fold_text(row.iloc[0] if len(row) > 0 else None)
        f1 = fold_text(row.iloc[1] if len(row) > 1 else None)
        if f0 == "TOTAL" or f1 == "TOTAL":
            total_idx = idx
            break
    if total_idx is None:
        raise ValueError("No se encontro TOTAL en causas")
    row = df.iloc[total_idx]
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


def parse_calificacion_simple(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_candidates = [
        idx
        for idx in range(min(25, len(df)))
        if fold_text(df.iloc[idx, 0]).startswith("PROCEDENCIA")
    ]
    start_row = start_candidates[-1] if start_candidates else find_row_with_token(df, "PROCEDENCIA", 0)
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[start_row + 1 :].iterrows():
        category = normalize_text(row.iloc[0] if len(row) > 0 else None)
        if not category:
            continue
        folded = fold_text(category)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "CUADRO"]):
            continue
        numeric_values = [as_number(value) for value in row.iloc[1:].tolist()]
        numeric_values = [value for value in numeric_values if value is not None]
        if len(numeric_values) < 3:
            continue
        huelgas, trabajadores, horas = numeric_values[:3]
        if is_total_label(category):
            totals = {
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
        )
    return rows, totals


def parse_organizacion_series(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    year_row = next(
        idx
        for idx in range(min(25, len(df)))
        if sum(1 for value in df.iloc[idx].tolist() if year_matches(value, year)) >= 3
    )
    positions = [idx for idx, value in enumerate(df.iloc[year_row].tolist()) if year_matches(value, year)]
    if len(positions) < 3:
        raise ValueError(f"No se encontraron tres columnas para {year} en organizacion")
    pct_cols = []
    for pos in positions[:3]:
        probe = normalize_text(df.iloc[year_row, pos + 1] if pos + 1 < len(df.columns) else None)
        pct_cols.append(pos + 1 if probe == "%" else None)
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[year_row + 1 :].iterrows():
        category = normalize_text(row.iloc[0] if len(row) > 0 else None)
        if not category:
            continue
        folded = fold_text(category)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "CUADRO"]):
            continue
        huelgas = as_number(row.iloc[positions[0]])
        trabajadores = as_number(row.iloc[positions[1]])
        horas = as_number(row.iloc[positions[2]])
        if is_total_label(category):
            totals = {
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
            continue
        if huelgas is None and trabajadores is None and horas is None:
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "pct_huelgas": as_number(row.iloc[pct_cols[0]]) if pct_cols[0] is not None else None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": as_number(row.iloc[pct_cols[1]]) if pct_cols[1] is not None else None,
                "horas_hombre_perdidas": horas,
                "pct_horas": as_number(row.iloc[pct_cols[2]]) if pct_cols[2] is not None else None,
            }
        )
    return rows, totals


def parse_organizacion_simple(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_row = find_row_with_token(df, "ORGANIZACION")
    if year == 1998:
        return parse_fixed_table(df, start_row, 1, 2, 4, 6, 3, 5, 7)
    return parse_fixed_table(df, start_row, 1, 2, 6, 10, 4, 8, 12)


def parse_tamano_old(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_row = find_row_with_token(df, "NUMERO DE TRABAJADORES", 0)
    return parse_fixed_table(df, start_row, 0, 1, 6, 11, 3, 8, 13)


def parse_duracion_old(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    start_row = find_row_with_token(df, "DURACION")
    if year == 1999:
        return parse_fixed_table(df, start_row, 1, 2, 6, 10, 4, 8, 12)
    return parse_fixed_table(df, start_row, 0, 1, 3, 5, 2, 4, 6)


def parse_territorio_old(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    if year == 1999:
        start_row = find_row_with_token(df, "DIRECCIONES REGIONALES", 1)
        return parse_fixed_table(df, start_row, 1, 2, 6, 10, 4, 8, 12)
    start_row = find_row_with_token(df, "REGIONES", 0)
    return parse_fixed_table(df, start_row, 0, 1, 3, 5, 2, 4, 6)


def homologate_activity_old(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "PARO CIVICO NACIONAL" in folded or "PAROS NACIONALES" in folded:
        return "paro_nacional", "paro_nacional", "paro civico/paros nacionales -> paro_nacional"
    if "SERVICIOS COMUNALES" in folded or "SERVICIOS SOCIALES Y COMUNALES" in folded:
        return "salud_social", "salud_social", "servicios comunales/sociales -> salud_social"
    if "SERVICIOS SOC." in normalize_text(label) or "SERVICIOS SOCIALES Y SALUD" in folded:
        return "salud_social", "salud_social", "servicios sociales y salud -> salud_social"
    if "AGRICULTURA" in folded:
        return "agricultura", "agricultura", "agricultura -> agricultura"
    if folded == "PESCA":
        return "pesca", "pesca", "pesca -> pesca"
    if "MINAS Y CANTERAS" in folded:
        return "mineria", "mineria", "minas y canteras/extraccion de petroleo -> mineria"
    if "MANUFACTUR" in folded:
        return "manufactura", "manufactura", "manufactura -> manufactura"
    if "ELECTRICIDAD" in folded or "GAS Y AGUA" in folded:
        return "electricidad_agua", "electricidad_agua", "electricidad/gas/agua -> electricidad_agua"
    if "CONSTRUCCION" in folded:
        return "construccion", "construccion", "construccion -> construccion"
    if "TRANSPORTE" in folded or "COMUNICACIONES" in folded:
        return "transporte", "transporte", "transporte/comunicaciones -> transporte"
    if "INTERMEDIACION FINANCIERA" in folded or "ESTABLEC." in normalize_text(label):
        return "financiero", "financiero", "intermediacion financiera/establecimientos financieros -> financiero"
    if "COMERCIO" in folded or "HOTELES" in folded or "REST." in normalize_text(label):
        return "comercio", "comercio", "comercio/restaurantes/hoteles -> comercio"
    if "INMOBILIARI" in folded or "ALQUILER" in folded:
        return "inmobiliario", "inmobiliario", "inmobiliario/alquiler -> inmobiliario"
    if "ENSENANZA" in folded:
        return "ensenanza", "ensenanza", "ensenanza -> ensenanza"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_organizacion_old(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "CONFEDERACION" in folded:
        return "confederacion", "confederacion", "confederacion(es) -> confederacion"
    if "FEDERACION" in folded:
        return "federacion", "federacion", "federacion(es) -> federacion"
    if "SINDICATO DE EMPLEADOS" in folded:
        return "sindicato_empleados", "sindicato_empleados", "sindicato de empleados -> sindicato_empleados"
    if "SINDICATO DE OBREROS" in folded:
        return "sindicato_obreros", "sindicato_obreros", "sindicato de obreros -> sindicato_obreros"
    if "SINDICATO UNICO" in folded:
        return "sindicato_unico", "sindicato_unico", "sindicato unico -> sindicato_unico"
    if "DELEGADOS DE EMPLEADOS" in folded:
        return "delegados_empleados", "delegados_empleados", "delegados de empleados -> delegados_empleados"
    if "DELEGADOS DE OBREROS" in folded:
        return "delegados_obreros", "delegados_obreros", "delegados de obreros -> delegados_obreros"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_duracion_old(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if folded == "UN DIA":
        return "1_dia", "1_dia", "un dia -> 1_dia"
    if folded == "DOS DIAS":
        return "2_dias", "2_3_dias", "dos dias -> fina 2_dias; agregada 2_3_dias"
    if folded == "TRES DIAS":
        return "3_dias", "2_3_dias", "tres dias -> fina 3_dias; agregada 2_3_dias"
    if "CUATRO A SIETE" in folded:
        return "4_7_dias", "4_7_dias", "cuatro a siete dias -> 4_7_dias"
    if "OCHO A QUINCE" in folded:
        return "8_15_dias", "8_15_dias", "ocho a quince dias -> 8_15_dias"
    if "DIECISEIS A TREINTA" in folded:
        return "16_30_dias", "16_mas_dias", "dieciseis a treinta dias -> fina 16_30_dias; agregada 16_mas_dias"
    if "MAS DE TREINTA" in folded:
        return "mas_30_dias", "16_mas_dias", "mas de treinta dias -> fina mas_30_dias; agregada 16_mas_dias"
    if "DIECISEIS DIAS A MAS" in folded or "DIESISEIS DIAS A MAS" in folded:
        return "16_mas_dias", "16_mas_dias", "dieciseis dias a mas -> 16_mas_dias"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_territorio_old(
    anio: int,
    label: str,
    current_parent: str | None,
) -> tuple[str, str, str, str | None, str]:
    clean = normalize_text(label).lstrip("-").strip()
    folded = fold_text(clean)
    if anio == 1999:
        headers = TERRITORY_HEADERS_1999
        if folded in headers and current_parent != slug_text(clean):
            slug = slug_text(clean)
            return slug, slug, "regional", slug, f"{clean} -> direccion regional; se preserva el doble registro regional/zona"
        slug = slug_text(clean)
        parent = current_parent or "sin_region_padre"
        return slug, slug, "zona", parent, f"{clean} -> zona de trabajo; region_madre={parent}"

    headers = TERRITORY_HEADERS_OLD[anio]
    if folded in headers and current_parent != slug_text(clean):
        slug = slug_text(clean)
        return slug, slug, "regional", slug, f"{clean} -> cabecera territorial historica; se preserva sin forzar equivalencia moderna"
    slug = slug_text(clean)
    parent = current_parent or "sin_region_padre"
    if current_parent == slug:
        return slug, slug, "zona", parent, f"{clean} -> ciudad/zona con mismo nombre que la cabecera territorial; region_madre={parent}"
    return slug, slug, "zona", parent, f"{clean} -> ciudad/zona historica; region_madre={parent}"


def build_module(
    anio: int,
    modulo: str,
    hoja_excel: str,
    rows: list[dict[str, object]],
    totals: dict[str, float | None],
    notes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[ValidationRow]]:
    output_rows: list[dict[str, object]] = []
    rules: list[dict[str, object]] = []
    current_parent: str | None = None
    note_text = " | ".join(notes)
    for row in rows:
        original = normalize_text(row["categoria_original"])
        nivel = None
        parent = None
        if modulo == "actividad":
            fina, agregada, regla = homologate_activity_old(original)
        elif modulo == "causas":
            fina, agregada, regla = homologate_causa(original)
        elif modulo == "calificacion":
            fina, agregada, regla = homologate_calificacion(original)
        elif modulo == "organizacion":
            fina, agregada, regla = homologate_organizacion_old(original)
        elif modulo == "tamano":
            fina, agregada, regla = homologate_tamano(original)
        elif modulo == "duracion":
            fina, agregada, regla = homologate_duracion_old(original)
        elif modulo == "territorio":
            fina, agregada, nivel, parent, regla = homologate_territorio_old(anio, original, current_parent)
            if nivel == "regional":
                current_parent = fina
        else:
            raise ValueError(modulo)

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
                "flag_hhp_arrastre": 0,
                "flag_faltante_fuente": 0,
                "flag_paro_nacional_registrado_lima": 0,
                "nota_fuente": note_text,
            }
        )

    module_df = pd.DataFrame(output_rows, columns=MODULE_COLUMNS)
    rules_df = pd.DataFrame(rules).drop_duplicates()
    validations = validate_module(anio, modulo, hoja_excel, module_df, totals)
    return module_df, rules_df, validations


def process_year(anio: int, config: dict[str, object]) -> None:
    path = config["path"]
    sheets: dict[str, str] = config["sheets"]  # type: ignore[assignment]

    module_frames: dict[str, pd.DataFrame] = {}
    rules_frames: list[pd.DataFrame] = []
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []

    for modulo in MODULE_ORDER:
        hoja = sheets[modulo]
        df_raw = pd.read_excel(path, sheet_name=hoja, header=None)
        notes = extract_tail_notes(df_raw)
        notes.append(YEAR_NOTES[anio][modulo])

        if modulo == "actividad":
            rows, totals = parse_activity_old(df_raw)
        elif modulo == "territorio":
            rows, totals = parse_territorio_old(df_raw, anio)
        elif modulo == "causas":
            rows, totals = parse_causas_9697(df_raw) if anio in {1996, 1997} else parse_causas_9899(df_raw)
        elif modulo == "calificacion":
            rows, totals = parse_calificacion_simple(df_raw)
        elif modulo == "organizacion":
            rows, totals = parse_organizacion_series(df_raw, anio) if anio in {1996, 1997} else parse_organizacion_simple(df_raw, anio)
        elif modulo == "tamano":
            rows, totals = parse_tamano_old(df_raw)
        elif modulo == "duracion":
            rows, totals = parse_duracion_old(df_raw, anio)
        else:
            raise ValueError(modulo)

        module_df, rules_df, validations = build_module(anio, modulo, hoja, rows, totals, notes)
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
                "validaciones_revisar": int(pd.DataFrame([row.__dict__ for row in validation_rows])["estado"].eq("revisar").sum()),
                "notas_fuente": len(notes_rows),
                "tipo_anio": "completo_layout_antiguo",
            }
        ]
    )
    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    dictionary_df = pd.concat(rules_frames, ignore_index=True).drop_duplicates()
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen", index=False)
        for modulo in MODULE_ORDER:
            module_frames[modulo].to_excel(writer, sheet_name=modulo, index=False)
        dictionary_df.to_excel(writer, sheet_name="diccionario_aplicado", index=False)
        notes_df.to_excel(writer, sheet_name="observaciones_fuente", index=False)
        validation_df.to_excel(writer, sheet_name="validacion", index=False)
    print(f"[ok] {anio} -> {excel_path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for anio, config in YEAR_CONFIG.items():
        process_year(anio, config)


if __name__ == "__main__":
    main()
