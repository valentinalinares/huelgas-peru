from __future__ import annotations

from pathlib import Path

import pandas as pd

from extract_era3_huelgas import (
    ROOT,
    ValidationRow,
    as_number,
    extract_tail_notes,
    fold_text,
    homologate_activity as base_homologate_activity,
    homologate_causa,
    homologate_organizacion as base_homologate_organizacion,
    normalize_text,
    rule_row,
    safe_diff,
    slug_text,
)


OUTPUT_DIR = ROOT / "bases" / "era1_homologados"
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
    1994: {
        "path": ROOT / "anuarios" / "1994" / "I-Ahuelga.xls",
        "sheets": {
            "actividad": "C-3",
            "causas": "C-9",
            "organizacion": "C-14",
            "territorio": "C-15",
        },
        "notes": {
            "actividad": "1994: actividad recuperada desde serie anual 1991-1995; se toma solo la columna 1994.",
            "causas": "1994: causas recuperadas desde serie anual 1987-1995; se toma solo la fila 1994.",
            "organizacion": "1994: organizacion recuperada desde serie 1994-1995; se toman solo las columnas 1994.",
            "territorio": "1994: territorio recuperado desde cuadro anual; mantiene geografia historica y estructura mixta region/ciudad.",
        },
    },
    1995: {
        "path": ROOT / "anuarios" / "1995" / "A-HUELGA.XLS",
        "sheets": {
            "actividad": "C-2",
            "causas": "C-7",
            "organizacion": "C-10",
            "territorio": "C-12",
        },
        "notes": {
            "actividad": "1995: actividad recuperada desde serie anual 1991-1995; se toma solo la columna 1995.",
            "causas": "1995: causas recuperadas desde tabla mensual; se toma la fila TOTAL del ano 1995.",
            "organizacion": "1995: organizacion recuperada desde serie 1994-1995; se toman solo las columnas 1995.",
            "territorio": "1995: territorio recuperado desde cuadro anual; mantiene geografia historica y estructura mixta region/ciudad.",
        },
    },
}

EXCLUDED_YEARS = {
    1993: {
        "source_dir": ROOT / "anuarios" / "1993",
        "reason": "1993: no existe workbook de huelgas en formato Excel; solo hay archivos .DOC, por lo que el ano queda fuera del pipeline tabular.",
    }
}


ERA1_REGION_HEADERS = {
    "INKA": "inka",
    "AREQUIPA": "arequipa",
    "SAN MARTIN": "san_martin",
    "NOR ORIENTAL DEL MARANON": "nor_oriental_del_maranon",
    "NOR ORIENTAL DEL MARAÑON": "nor_oriental_del_maranon",
    "LA LIBERTAD": "la_libertad",
    "GRAU": "grau",
    "CHAVIN": "chavin",
    "LORETO": "loreto",
    "ANDRES A. CACERES": "andres_a_caceres",
    "LIBERTADORES WARI": "libertadores_wari",
    "MOQUEGUA TACNA PUNO": "moquegua_tacna_puno",
    "MOQUEGUA - TACNA - PUNO": "moquegua_tacna_puno",
    "LIMA": "lima",
}


def is_total_label(value: object) -> bool:
    return fold_text(value).replace(" ", "") == "TOTAL"


def year_matches(value: object, year: int) -> bool:
    text = normalize_text(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text in {str(year), str(year)[-2:]}


def empty_module_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=MODULE_COLUMNS)


def unavailable_validations(anio: int, modulo: str) -> list[ValidationRow]:
    return [
        ValidationRow(
            anio=anio,
            modulo=modulo,
            hoja_excel="N/A",
            metrica=metric,
            total_extraido=None,
            total_fuente=None,
            diferencia=None,
            estado="no_disponible",
        )
        for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
    ]


def validate_module(
    anio: int,
    modulo: str,
    hoja_excel: str,
    df: pd.DataFrame,
    totals: dict[str, float | None],
) -> list[ValidationRow]:
    if modulo == "territorio":
        return [
            ValidationRow(
                anio=anio,
                modulo=modulo,
                hoja_excel=hoja_excel,
                metrica=f"{metric}_todos_los_niveles",
                total_extraido=None
                if pd.isna(pd.to_numeric(df[metric], errors="coerce").sum(min_count=1))
                else float(pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)),
                total_fuente=totals.get(metric),
                diferencia=safe_diff(
                    None
                    if pd.isna(pd.to_numeric(df[metric], errors="coerce").sum(min_count=1))
                    else float(pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)),
                    totals.get(metric),
                ),
                estado="estructura_mixta",
            )
            for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
    rows: list[ValidationRow] = []
    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        extracted = pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)
        extracted_value = None if pd.isna(extracted) else float(extracted)
        source_value = totals.get(metric)
        diff = safe_diff(extracted_value, source_value)
        state = "ok" if diff is not None and abs(diff) <= 0.01 else "revisar"
        rows.append(
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
    return rows


def homologate_activity_era1(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "SERVICIOS COMUNALES Y SOCIALES" in folded:
        return "salud_social", "salud_social", "servicios comunales y sociales -> salud_social"
    if "PAROS NACIONALES" in folded:
        return "paro_nacional", "paro_nacional", "paros nacionales -> paro_nacional"
    return base_homologate_activity(label)


def homologate_organizacion_era1(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "CONFEDERACION" in folded:
        return "confederacion", "confederacion", "confederacion(es) -> confederacion"
    return base_homologate_organizacion(label)


def homologate_territorio_era1(
    label: str,
    current_parent: str | None,
) -> tuple[str, str, str, str | None, str]:
    original = normalize_text(label)
    clean = original.lstrip("-").strip()
    folded = fold_text(clean)
    if folded in ERA1_REGION_HEADERS:
        region_slug = ERA1_REGION_HEADERS[folded]
        if current_parent == region_slug:
            return (
                region_slug,
                region_slug,
                "zona",
                region_slug,
                f"{clean} -> ciudad/zona con mismo nombre que la region historica; region_madre={region_slug}",
            )
        return (
            region_slug,
            region_slug,
            "regional",
            region_slug,
            f"{clean} -> region historica/agrupacion territorial; se preserva sin forzar equivalencia moderna",
        )
    zona_slug = slug_text(clean)
    parent_slug = current_parent or "sin_region_padre"
    return (
        zona_slug,
        zona_slug,
        "zona",
        parent_slug,
        f"{clean} -> ciudad/zona historica; region_madre={parent_slug}",
    )


def base_row(
    anio: int,
    modulo: str,
    hoja_excel: str,
    original: str,
    fina: str,
    agregada: str,
    regla: str,
    note: str,
    huelgas: float | None,
    trabajadores: float | None,
    horas: float | None,
    pct_huelgas: float | None = None,
    pct_trabajadores: float | None = None,
    pct_horas: float | None = None,
    nivel: str | None = None,
    parent: str | None = None,
) -> dict[str, object]:
    return {
        "anio": anio,
        "modulo": modulo,
        "hoja_excel": hoja_excel,
        "categoria_original": original,
        "categoria_homologada_fina": fina,
        "categoria_homologada_agregada": agregada,
        "regla_homologacion": regla,
        "nivel_territorial": nivel,
        "territorio_padre": parent,
        "huelgas": huelgas,
        "pct_huelgas": pct_huelgas,
        "trabajadores_comprendidos": trabajadores,
        "pct_trabajadores": pct_trabajadores,
        "horas_hombre_perdidas": horas,
        "pct_horas": pct_horas,
        "flag_hhp_arrastre": 0,
        "flag_faltante_fuente": 0,
        "flag_paro_nacional_registrado_lima": 0,
        "nota_fuente": note,
    }


def parse_activity_series(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = next(
        idx
        for idx in range(min(20, len(df)))
        if "ACTIVIDAD" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
        and "TRABAJADORES" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
    )
    year_row = header_row + 1
    category_col = min(idx for idx, value in enumerate(df.iloc[header_row].tolist()) if normalize_text(value))
    positions = [idx for idx, value in enumerate(df.iloc[year_row].tolist()) if year_matches(value, year)]
    if len(positions) < 3:
        raise ValueError(f"No se encontraron las tres columnas del ano {year} en actividad")
    huelgas_col, trabajadores_col, horas_col = positions[:3]

    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[year_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category:
            continue
        folded = fold_text(category)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "PAG."]):
            continue
        huelgas = as_number(row.iloc[huelgas_col] if huelgas_col < len(row) else None)
        trabajadores = as_number(row.iloc[trabajadores_col] if trabajadores_col < len(row) else None)
        horas = as_number(row.iloc[horas_col] if horas_col < len(row) else None)
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
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
        )
    return rows, totals


def parse_organizacion_series(df: pd.DataFrame, year: int) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = next(
        idx
        for idx in range(min(20, len(df) - 1))
        if "ORGANIZACION" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
        and sum(1 for value in df.iloc[idx + 1].tolist() if year_matches(value, year)) >= 2
    )
    year_row = header_row + 1
    category_col = min(idx for idx, value in enumerate(df.iloc[header_row].tolist()) if normalize_text(value))
    positions = [idx for idx, value in enumerate(df.iloc[year_row].tolist()) if year_matches(value, year)]
    if len(positions) < 3:
        raise ValueError(f"No se encontraron las tres columnas del ano {year} en organizacion")
    huelgas_col, trabajadores_col, horas_col = positions[:3]

    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[year_row + 1 :].iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category:
            continue
        folded = fold_text(category)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "PAG."]):
            continue
        huelgas = as_number(row.iloc[huelgas_col] if huelgas_col < len(row) else None)
        trabajadores = as_number(row.iloc[trabajadores_col] if trabajadores_col < len(row) else None)
        horas = as_number(row.iloc[horas_col] if horas_col < len(row) else None)
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
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
        )
    return rows, totals


def parse_causas_1994(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    target = None
    for _, row in df.iterrows():
        if normalize_text(row.iloc[1] if len(row) > 1 else None) == "1994":
            target = row
            break
    if target is None:
        raise ValueError("No se encontro la fila 1994 en causas")
    rows = [
        {
            "categoria_original": "PLIEGO RECLAMOS",
            "huelgas": as_number(target.iloc[2]),
            "trabajadores_comprendidos": as_number(target.iloc[5]),
            "horas_hombre_perdidas": as_number(target.iloc[8]),
        },
        {
            "categoria_original": "OTRAS CAUSAS",
            "huelgas": as_number(target.iloc[3]),
            "trabajadores_comprendidos": as_number(target.iloc[6]),
            "horas_hombre_perdidas": as_number(target.iloc[9]),
        },
    ]
    totals = {
        "huelgas": as_number(target.iloc[4]),
        "trabajadores_comprendidos": as_number(target.iloc[7]),
        "horas_hombre_perdidas": as_number(target.iloc[10]),
    }
    return rows, totals


def parse_causas_1995(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    target = None
    for _, row in df.iterrows():
        if is_total_label(row.iloc[2] if len(row) > 2 else None):
            target = row
            break
    if target is None:
        raise ValueError("No se encontro TOTAL en causas 1995")
    rows = [
        {
            "categoria_original": "PLIEGO RECLAMOS",
            "huelgas": as_number(target.iloc[3]),
            "pct_huelgas": as_number(target.iloc[4]),
            "trabajadores_comprendidos": as_number(target.iloc[9]),
            "pct_trabajadores": as_number(target.iloc[10]),
            "horas_hombre_perdidas": as_number(target.iloc[15]),
            "pct_horas": as_number(target.iloc[16]),
        },
        {
            "categoria_original": "OTRAS CAUSAS",
            "huelgas": as_number(target.iloc[5]),
            "pct_huelgas": as_number(target.iloc[6]),
            "trabajadores_comprendidos": as_number(target.iloc[11]),
            "pct_trabajadores": as_number(target.iloc[12]),
            "horas_hombre_perdidas": as_number(target.iloc[17]),
            "pct_horas": as_number(target.iloc[18]),
        },
    ]
    totals = {
        "huelgas": as_number(target.iloc[7]),
        "trabajadores_comprendidos": as_number(target.iloc[13]),
        "horas_hombre_perdidas": as_number(target.iloc[19]),
    }
    return rows, totals


def parse_territorio_era1(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = next(
        idx
        for idx in range(min(20, len(df)))
        if "REGIONES / CIUDADES" in fold_text(" ".join(normalize_text(v) for v in df.iloc[idx].tolist() if normalize_text(v)))
    )
    rows_raw: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[header_row + 1 :].iterrows():
        label = normalize_text(row.iloc[0] if len(row) > 0 else None)
        huelgas = as_number(row.iloc[1] if len(row) > 1 else None)
        pct_huelgas = as_number(row.iloc[2] if len(row) > 2 else None)
        trabajadores = as_number(row.iloc[3] if len(row) > 3 else None)
        pct_trabajadores = as_number(row.iloc[4] if len(row) > 4 else None)
        horas = as_number(row.iloc[5] if len(row) > 5 else None)
        pct_horas = as_number(row.iloc[6] if len(row) > 6 else None)
        if not label:
            continue
        folded = fold_text(label)
        if any(token in folded for token in ["FUENTE", "ELABORADO", "OFICINA", "PAG."]):
            continue
        if is_total_label(label):
            totals = {
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
            }
            continue
        if huelgas is None and trabajadores is None and horas is None:
            if rows_raw:
                rows_raw[-1]["categoria_original"] = f"{rows_raw[-1]['categoria_original']} {label}"
            continue
        rows_raw.append(
            {
                "categoria_original": label,
                "huelgas": huelgas,
                "pct_huelgas": pct_huelgas,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": pct_trabajadores,
                "horas_hombre_perdidas": horas,
                "pct_horas": pct_horas,
            }
        )
    return rows_raw, totals


def build_available_module(
    anio: int,
    modulo: str,
    hoja_excel: str,
    rows: list[dict[str, object]],
    totals: dict[str, float | None],
    notes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[ValidationRow]]:
    output_rows: list[dict[str, object]] = []
    rules: list[dict[str, object]] = []
    note_text = " | ".join(notes)
    current_parent: str | None = None
    for row in rows:
        original = normalize_text(row["categoria_original"])
        nivel = None
        parent = None
        if modulo == "actividad":
            fina, agregada, regla = homologate_activity_era1(original)
        elif modulo == "causas":
            fina, agregada, regla = homologate_causa(original)
        elif modulo == "organizacion":
            fina, agregada, regla = homologate_organizacion_era1(original)
        elif modulo == "territorio":
            fina, agregada, nivel, parent, regla = homologate_territorio_era1(original, current_parent)
            if nivel == "regional":
                current_parent = fina
        else:
            raise ValueError(modulo)
        rules.append(rule_row(anio, modulo, original, fina, agregada, regla))
        output_rows.append(
            base_row(
                anio=anio,
                modulo=modulo,
                hoja_excel=hoja_excel,
                original=original,
                fina=fina,
                agregada=agregada,
                regla=regla,
                note=note_text,
                huelgas=row.get("huelgas"),
                trabajadores=row.get("trabajadores_comprendidos"),
                horas=row.get("horas_hombre_perdidas"),
                pct_huelgas=row.get("pct_huelgas"),
                pct_trabajadores=row.get("pct_trabajadores"),
                pct_horas=row.get("pct_horas"),
                nivel=nivel,
                parent=parent,
            )
        )
    module_df = pd.DataFrame(output_rows, columns=MODULE_COLUMNS)
    rules_df = pd.DataFrame(rules).drop_duplicates()
    validations = validate_module(anio, modulo, hoja_excel, module_df, totals)
    return module_df, rules_df, validations


def process_year(anio: int, config: dict[str, object]) -> None:
    path = config["path"]
    sheets: dict[str, str] = config["sheets"]  # type: ignore[assignment]
    year_notes: dict[str, str] = config["notes"]  # type: ignore[assignment]

    module_frames: dict[str, pd.DataFrame] = {modulo: empty_module_frame() for modulo in MODULE_ORDER}
    rules_frames: list[pd.DataFrame] = []
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []

    for modulo in MODULE_ORDER:
        if modulo not in sheets:
            validation_rows.extend(unavailable_validations(anio, modulo))
            notes_rows.append(
                {
                    "anio": anio,
                    "modulo": modulo,
                    "hoja_excel": "N/A",
                    "nota_fuente": f"{anio}: modulo no disponible en el workbook original.",
                }
            )
            continue

        hoja = sheets[modulo]
        df_raw = pd.read_excel(path, sheet_name=hoja, header=None)
        notes = extract_tail_notes(df_raw)
        notes.append(year_notes[modulo])

        if modulo == "actividad":
            rows, totals = parse_activity_series(df_raw, anio)
        elif modulo == "causas":
            rows, totals = parse_causas_1994(df_raw) if anio == 1994 else parse_causas_1995(df_raw)
        elif modulo == "organizacion":
            rows, totals = parse_organizacion_series(df_raw, anio)
        elif modulo == "territorio":
            rows, totals = parse_territorio_era1(df_raw)
        else:
            raise ValueError(modulo)

        module_df, rules_df, validations = build_available_module(anio, modulo, hoja, rows, totals, notes)
        module_frames[modulo] = module_df
        rules_frames.append(rules_df)
        validation_rows.extend(validations)
        for note in notes:
            notes_rows.append({"anio": anio, "modulo": modulo, "hoja_excel": hoja, "nota_fuente": note})

    excel_path = OUTPUT_DIR / f"huelgas_{anio}_homologado.xlsx"
    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    dictionary_df = (
        pd.concat(rules_frames, ignore_index=True).drop_duplicates()
        if rules_frames
        else pd.DataFrame(columns=["anio", "modulo", "categoria_original", "categoria_homologada_fina", "categoria_homologada_agregada", "regla_homologacion"])
    )
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()
    summary_df = pd.DataFrame(
        [
            {
                "anio": anio,
                "archivo_fuente": str(path.relative_to(ROOT)),
                "archivo_salida": str(excel_path.relative_to(ROOT)),
                "modulos_generados": len(MODULE_ORDER),
                "modulos_disponibles": sum(1 for modulo in MODULE_ORDER if modulo in sheets),
                "modulos_no_disponibles": sum(1 for modulo in MODULE_ORDER if modulo not in sheets),
                "filas_totales": sum(len(frame) for frame in module_frames.values()),
                "validaciones_revisar": int(validation_df["estado"].eq("revisar").sum()) if not validation_df.empty else 0,
                "notas_fuente": len(notes_df),
                "tipo_anio": "parcial",
            }
        ]
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen", index=False)
        for modulo in MODULE_ORDER:
            module_frames[modulo].to_excel(writer, sheet_name=modulo, index=False)
        dictionary_df.to_excel(writer, sheet_name="diccionario_aplicado", index=False)
        notes_df.to_excel(writer, sheet_name="observaciones_fuente", index=False)
        validation_df.to_excel(writer, sheet_name="validacion", index=False)
    print(f"[ok] {anio} -> {excel_path}")


def process_excluded_year(anio: int, config: dict[str, object]) -> None:
    source_dir: Path = config["source_dir"]  # type: ignore[assignment]
    reason: str = config["reason"]  # type: ignore[assignment]
    excel_path = OUTPUT_DIR / f"huelgas_{anio}_homologado.xlsx"

    module_frames: dict[str, pd.DataFrame] = {modulo: empty_module_frame() for modulo in MODULE_ORDER}
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []

    source_files = sorted(path.name for path in source_dir.glob("*.DOC"))
    source_listing = ", ".join(source_files) if source_files else "sin archivos .DOC listados"

    for modulo in MODULE_ORDER:
        validation_rows.extend(unavailable_validations(anio, modulo))
        notes_rows.append(
            {
                "anio": anio,
                "modulo": modulo,
                "hoja_excel": "N/A",
                "nota_fuente": f"{reason} Archivos detectados: {source_listing}",
            }
        )

    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    dictionary_df = pd.DataFrame(
        columns=[
            "anio",
            "modulo",
            "categoria_original",
            "categoria_homologada_fina",
            "categoria_homologada_agregada",
            "regla_homologacion",
        ]
    )
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()
    summary_df = pd.DataFrame(
        [
            {
                "anio": anio,
                "archivo_fuente": str(source_dir.relative_to(ROOT)),
                "archivo_salida": str(excel_path.relative_to(ROOT)),
                "modulos_generados": len(MODULE_ORDER),
                "modulos_disponibles": 0,
                "modulos_no_disponibles": len(MODULE_ORDER),
                "filas_totales": 0,
                "validaciones_revisar": 0,
                "notas_fuente": len(notes_df),
                "tipo_anio": "excluido_sin_excel_fuente",
            }
        ]
    )

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
    for anio, config in EXCLUDED_YEARS.items():
        process_excluded_year(anio, config)
    for anio, config in YEAR_CONFIG.items():
        process_year(anio, config)


if __name__ == "__main__":
    main()
