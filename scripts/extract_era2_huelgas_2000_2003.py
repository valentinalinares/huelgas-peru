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
    homologate_territorio,
    normalize_text,
    rule_row,
)
from extract_era2_huelgas_2004_2020 import parse_causas, parse_calificacion, validate_module


OUTPUT_DIR = ROOT / "bases" / "era2_homologados_2000_2003"
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
    2000: {
        "path": ROOT / "anuarios" / "2000" / "I-HUELGA2000.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-10",
            "duracion": "C-9",
        },
        "notes": {
            "actividad": "2000: actividad leida con layout fijo antiguo; se ignoran bloques laterales y porcentajes fuera del cuadro principal.",
            "territorio": "2000: territorio leido con layout fijo de direcciones regionales y zonas de trabajo; se mantiene estructura mixta.",
            "causas": "2000: causas leidas desde la fila TOTAL del cuadro mensual C-6.",
            "calificacion": "2000: calificacion leida desde C-7.",
            "organizacion": "2000: organizacion leida con layout fijo antiguo; el cuadro anual no incluye todas las formas sindicales posteriores.",
            "tamano": "2000: tamano leido desde C-10; en este ano tamano y duracion estan invertidos respecto del esquema posterior.",
            "duracion": "2000: duracion leida desde C-9; en este ano tamano y duracion estan invertidos respecto del esquema posterior.",
        },
    },
    2001: {
        "path": ROOT / "anuarios" / "2001" / "I-HUELGA2001.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-10",
            "duracion": "C-9",
        },
        "notes": {
            "actividad": "2001: actividad leida con layout fijo antiguo.",
            "territorio": "2001: territorio leido con layout fijo; se mantiene estructura mixta region/zona.",
            "causas": "2001: causas leidas desde la fila TOTAL del cuadro mensual C-6.",
            "calificacion": "2001: calificacion leida desde C-7.",
            "organizacion": "2001: organizacion leida con layout fijo antiguo; el TOTAL esta en una columna distinta al texto de categoria.",
            "tamano": "2001: tamano leido desde C-10; tamano y duracion siguen invertidos respecto del esquema posterior.",
            "duracion": "2001: duracion leida desde C-9; tamano y duracion siguen invertidos respecto del esquema posterior.",
        },
    },
    2002: {
        "path": ROOT / "anuarios" / "2002" / "CAPITULO I - HUELGA 2002.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-9",
            "duracion": "C-10",
        },
        "notes": {
            "actividad": "2002: actividad leida con layout fijo del bloque intermedio.",
            "territorio": "2002: territorio leido con layout fijo de direcciones regionales y zonas; se mantiene estructura mixta.",
            "causas": "2002: causas leidas desde la fila TOTAL del cuadro mensual C-6.",
            "calificacion": "2002: calificacion leida desde C-7.",
            "organizacion": "2002: organizacion leida con layout fijo intermedio.",
            "tamano": "2002: tamano leido desde C-9 con columnas desplazadas respecto del bloque posterior.",
            "duracion": "2002: duracion leida desde C-10; los tramos largos viejos se agregan a 16_mas_dias.",
        },
    },
    2003: {
        "path": ROOT / "anuarios" / "2003" / "CAPITULO I - HUELGA 2003.xls",
        "sheets": {
            "actividad": "C-3",
            "territorio": "C-5",
            "causas": "C-6",
            "calificacion": "C-7",
            "organizacion": "C-8",
            "tamano": "C-9",
            "duracion": "C-10",
        },
        "notes": {
            "actividad": "2003: actividad leida con layout fijo del bloque intermedio.",
            "territorio": "2003: territorio leido con layout fijo; se mantiene estructura mixta region/zona.",
            "causas": "2003: causas leidas desde la fila TOTAL del cuadro mensual C-6.",
            "calificacion": "2003: calificacion leida desde C-7.",
            "organizacion": "2003: organizacion leida con layout fijo simple.",
            "tamano": "2003: tamano leido desde C-9 con layout intermedio.",
            "duracion": "2003: duracion leida desde C-10; los tramos largos viejos se agregan a 16_mas_dias.",
        },
    },
}


FIXED_LAYOUTS: dict[int, dict[str, dict[str, int | list[int]]]] = {
    2000: {
        "actividad": {"start_row": 19, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 5, "pct_t_col": 7, "horas_col": 9, "pct_hh_col": 11, "total_label_cols": [0]},
        "territorio": {"start_row": 15, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "organizacion": {"start_row": 13, "category_col": 1, "huelgas_col": 2, "pct_h_col": 3, "trabajadores_col": 4, "pct_t_col": 5, "horas_col": 6, "pct_hh_col": 7, "total_label_cols": [0, 1]},
        "tamano": {"start_row": 15, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 11, "pct_hh_col": 13, "total_label_cols": [0]},
        "duracion": {"start_row": 14, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
    },
    2001: {
        "actividad": {"start_row": 17, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 5, "pct_t_col": 7, "horas_col": 9, "pct_hh_col": 11, "total_label_cols": [0]},
        "territorio": {"start_row": 15, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "organizacion": {"start_row": 14, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "tamano": {"start_row": 14, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 11, "pct_hh_col": 13, "total_label_cols": [0]},
        "duracion": {"start_row": 13, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
    },
    2002: {
        "actividad": {"start_row": 11, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 5, "pct_t_col": 7, "horas_col": 9, "pct_hh_col": 11, "total_label_cols": [0]},
        "territorio": {"start_row": 14, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "organizacion": {"start_row": 11, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "tamano": {"start_row": 14, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 7, "pct_t_col": 9, "horas_col": 12, "pct_hh_col": 14, "total_label_cols": [0, 1]},
        "duracion": {"start_row": 12, "category_col": 2, "huelgas_col": 3, "pct_h_col": 5, "trabajadores_col": 7, "pct_t_col": 9, "horas_col": 11, "pct_hh_col": 13, "total_label_cols": [0, 1, 2]},
    },
    2003: {
        "actividad": {"start_row": 5, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 5, "pct_t_col": 7, "horas_col": 9, "pct_hh_col": 11, "total_label_cols": [0]},
        "territorio": {"start_row": 5, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
        "organizacion": {"start_row": 5, "category_col": 1, "huelgas_col": 2, "pct_h_col": 3, "trabajadores_col": 4, "pct_t_col": 5, "horas_col": 6, "pct_hh_col": 7, "total_label_cols": [0, 1]},
        "tamano": {"start_row": 5, "category_col": 0, "huelgas_col": 1, "pct_h_col": 3, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 11, "pct_hh_col": 13, "total_label_cols": [0]},
        "duracion": {"start_row": 5, "category_col": 1, "huelgas_col": 2, "pct_h_col": 4, "trabajadores_col": 6, "pct_t_col": 8, "horas_col": 10, "pct_hh_col": 12, "total_label_cols": [0, 1]},
    },
}


def parse_fixed_table(
    df: pd.DataFrame,
    *,
    start_row: int,
    category_col: int,
    huelgas_col: int,
    trabajadores_col: int,
    horas_col: int,
    pct_h_col: int | None,
    pct_t_col: int | None,
    pct_hh_col: int | None,
    total_label_cols: list[int],
) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    rows: list[dict[str, object]] = []
    totals = {"huelgas": None, "trabajadores_comprendidos": None, "horas_hombre_perdidas": None}
    for _, row in df.iloc[start_row + 1 :].iterrows():
        total_found = False
        for probe_col in total_label_cols:
            if probe_col < len(row) and fold_text(row.iloc[probe_col]) == "TOTAL":
                total_found = True
                break
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category and not total_found:
            continue
        folded = fold_text(category if category else "TOTAL")
        if any(token in folded for token in ["FUENTE", "ELABORADO", "ELABORACION", "DIRECCION", "OFICINA", "NOTA", "CUADRO", "PERU"]):
            continue
        huelgas = as_number(row.iloc[huelgas_col] if huelgas_col < len(row) else None)
        trabajadores = as_number(row.iloc[trabajadores_col] if trabajadores_col < len(row) else None)
        horas = as_number(row.iloc[horas_col] if horas_col < len(row) else None)
        if total_found:
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
                "pct_huelgas": as_number(row.iloc[pct_h_col]) if pct_h_col is not None and pct_h_col < len(row) else None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": as_number(row.iloc[pct_t_col]) if pct_t_col is not None and pct_t_col < len(row) else None,
                "horas_hombre_perdidas": horas,
                "pct_horas": as_number(row.iloc[pct_hh_col]) if pct_hh_col is not None and pct_hh_col < len(row) else None,
            }
        )
    return rows, totals


def homologate_activity_mid(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if folded == "PAROS" or "PARO CIVICO NACIONAL" in folded or "PAROS NACIONALES" in folded or "PARO NACIONAL" in folded:
        return "paro_nacional", "paro_nacional", "paro civico/paros nacionales -> paro_nacional"
    if "SERVICIOS COMUNALES" in folded or "SERVICIOS SOCIALES Y COMUNALES" in folded:
        return "salud_social", "salud_social", "servicios comunales/sociales -> salud_social"
    if "SERVICIOS SOCIALES Y DE SALUD" in folded:
        return "salud_social", "salud_social", "servicios sociales y de salud -> salud_social"
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
    if "ADMINISTRACION PUBLICA" in folded:
        return "adm_publica", "adm_publica", "administracion publica -> adm_publica"
    if "ENSENANZA" in folded:
        return "ensenanza", "ensenanza", "ensenanza -> ensenanza"
    if "OTRAS ACTIV" in folded and ("SERVICIOS" in folded or "SERV." in normalize_text(label)):
        return "otros_servicios", "otros_servicios", "otras actividades de servicios -> otros_servicios"
    return normalize_text(label).lower().strip().replace(" ", "_"), normalize_text(label).lower().strip().replace(" ", "_"), "sin traduccion adicional; se normaliza el texto"


def homologate_organizacion_mid(label: str) -> tuple[str, str, str]:
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
    return normalize_text(label).lower().strip().replace(" ", "_"), normalize_text(label).lower().strip().replace(" ", "_"), "sin traduccion adicional; se normaliza el texto"


def homologate_duracion_mid(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if folded.startswith("UN DIA"):
        return "1_dia", "1_dia", "un dia -> 1_dia"
    if folded.startswith("DOS DIAS"):
        return "2_dias", "2_3_dias", "dos dias -> fina 2_dias; agregada 2_3_dias"
    if folded.startswith("TRES DIAS"):
        return "3_dias", "2_3_dias", "tres dias -> fina 3_dias; agregada 2_3_dias"
    if "CUATRO A SIETE" in folded:
        return "4_7_dias", "4_7_dias", "cuatro a siete dias -> 4_7_dias"
    if "OCHO A QUINCE" in folded:
        return "8_15_dias", "8_15_dias", "ocho a quince dias -> 8_15_dias"
    if "DIECISEIS A TREINTA" in folded:
        return "16_30_dias", "16_mas_dias", "dieciseis a treinta dias -> fina 16_30_dias; agregada 16_mas_dias"
    if "MAS DE 30" in folded or "MAS DE TREINTA" in folded:
        return "mas_30_dias", "16_mas_dias", "mas de 30 dias -> fina mas_30_dias; agregada 16_mas_dias"
    if "DIECISEIS DIAS A MAS" in folded or "DIESISEIS DIAS A MAS" in folded:
        return "16_mas_dias", "16_mas_dias", "dieciseis dias a mas -> 16_mas_dias"
    return normalize_text(label).lower().strip().replace(" ", "_"), normalize_text(label).lower().strip().replace(" ", "_"), "sin traduccion adicional; se normaliza el texto"


def slug_text_local(label: str) -> str:
    return normalize_text(label).lower().strip().replace(" ", "_")


def build_module_frame(anio: int, modulo: str, hoja_excel: str, df_raw: pd.DataFrame, year_note: str):
    notes = extract_tail_notes(df_raw)
    notes.append(year_note)
    rules: list[dict[str, object]] = []

    if modulo in FIXED_LAYOUTS[anio]:
        layout = FIXED_LAYOUTS[anio][modulo]
        rows, totals = parse_fixed_table(
            df_raw,
            start_row=int(layout["start_row"]),
            category_col=int(layout["category_col"]),
            huelgas_col=int(layout["huelgas_col"]),
            trabajadores_col=int(layout["trabajadores_col"]),
            horas_col=int(layout["horas_col"]),
            pct_h_col=int(layout["pct_h_col"]) if layout["pct_h_col"] is not None else None,
            pct_t_col=int(layout["pct_t_col"]) if layout["pct_t_col"] is not None else None,
            pct_hh_col=int(layout["pct_hh_col"]) if layout["pct_hh_col"] is not None else None,
            total_label_cols=list(layout["total_label_cols"]),
        )
    elif modulo == "causas":
        rows, totals = parse_causas(df_raw)
    elif modulo == "calificacion":
        rows, totals = parse_calificacion(df_raw)
    else:
        raise ValueError(modulo)

    current_region_slug = None
    output_rows: list[dict[str, object]] = []
    note_text = " | ".join(notes)
    for row in rows:
        original = normalize_text(row["categoria_original"])
        nivel = None
        parent = None
        if modulo == "actividad":
            fina, agregada, regla = homologate_activity_mid(original)
        elif modulo == "causas":
            fina, agregada, regla = homologate_causa(original)
        elif modulo == "calificacion":
            fina, agregada, regla = homologate_calificacion(original)
        elif modulo == "organizacion":
            fina, agregada, regla = homologate_organizacion_mid(original)
        elif modulo == "tamano":
            fina, agregada, regla = homologate_tamano(original)
        elif modulo == "duracion":
            fina, agregada, regla = homologate_duracion_mid(original)
        elif modulo == "territorio":
            fina, agregada, nivel, parent, regla = homologate_territorio(original, current_region_slug)
            if nivel == "regional":
                current_region_slug = fina
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
                "flag_hhp_arrastre": int(any("HORAS - HOMBRE PERDIDAS GENERADAS" in fold_text(note) for note in notes)),
                "flag_faltante_fuente": int(any("NO SE DISPONE" in fold_text(note) for note in notes)),
                "flag_paro_nacional_registrado_lima": 0,
                "nota_fuente": note_text,
            }
        )

    module_df = pd.DataFrame(output_rows, columns=MODULE_COLUMNS)
    rules_df = pd.DataFrame(rules).drop_duplicates()
    validations = validate_module(anio, modulo, hoja_excel, module_df, totals)
    return module_df, rules_df, validations, notes


def process_year(anio: int, config: dict[str, object]) -> None:
    path: Path = config["path"]  # type: ignore[assignment]
    sheets: dict[str, str] = config["sheets"]  # type: ignore[assignment]
    notes_map: dict[str, str] = config["notes"]  # type: ignore[assignment]

    module_frames: dict[str, pd.DataFrame] = {}
    rules_frames: list[pd.DataFrame] = []
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []

    for modulo in MODULE_ORDER:
        hoja = sheets[modulo]
        df_raw = pd.read_excel(path, sheet_name=hoja, header=None)
        module_df, rules_df, validations, notes = build_module_frame(anio, modulo, hoja, df_raw, notes_map[modulo])
        module_frames[modulo] = module_df
        rules_frames.append(rules_df)
        validation_rows.extend(validations)
        for note in notes:
            notes_rows.append({"anio": anio, "modulo": modulo, "hoja_excel": hoja, "nota_fuente": note})

    excel_path = OUTPUT_DIR / f"huelgas_{anio}_homologado.xlsx"
    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    dictionary_df = pd.concat(rules_frames, ignore_index=True).drop_duplicates()
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()
    summary_df = pd.DataFrame(
        [
            {
                "anio": anio,
                "archivo_fuente": str(path.relative_to(ROOT)),
                "archivo_salida": str(excel_path.relative_to(ROOT)),
                "modulos_generados": len(module_frames),
                "filas_totales": sum(len(df) for df in module_frames.values()),
                "validaciones_revisar": int(validation_df["estado"].eq("revisar").sum()) if not validation_df.empty else 0,
                "notas_fuente": len(notes_df),
                "tipo_anio": "completo",
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
    for anio, config in YEAR_CONFIG.items():
        process_year(anio, config)


if __name__ == "__main__":
    main()
