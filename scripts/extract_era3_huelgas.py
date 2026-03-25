from __future__ import annotations

import re
import unicodedata
import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


warnings.filterwarnings(
    "ignore",
    message="Unknown extension is not supported and will be removed",
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "bases" / "era3_homologados"


YEAR_CONFIG = {
    2021: {
        "path": ROOT / "anuarios" / "2021" / "CAPITULO 04 - HUELGAS.xlsx",
        "sheets": {
            "actividad": "C-84",
            "territorio": "C-93",
            "causas": "C-87",
            "calificacion": "C-88",
            "organizacion": "C-89",
            "tamano": "C-90",
            "duracion": "C-91",
            "cruce": "C-92",
        },
    },
    2022: {
        "path": ROOT / "anuarios" / "2022" / "CAPITULO 04 - HUELGAS.xlsx",
        "sheets": {
            "actividad": "C-93",
            "territorio": "C-95",
            "causas": "C-96",
            "calificacion": "C-97",
            "organizacion": "C-98",
            "tamano": "C-99",
            "duracion": "C-100",
            "cruce": "C-101",
        },
    },
    2023: {
        "path": ROOT
        / "anuarios"
        / "2023"
        / "anuarioestadisticosectorial2023archivosexcelypdf"
        / "CAPITULO 04 - HUELGAS_2023.xlsx",
        "sheets": {
            "actividad": "C-94",
            "territorio": "C-96",
            "causas": "C-97",
            "calificacion": "C-98",
            "organizacion": "C-99",
            "tamano": "C-100",
            "duracion": "C-101",
            "cruce": "C-102",
        },
    },
    2024: {
        "path": ROOT / "anuarios" / "2024" / "CAP 04 - HUELGAS_2024.xlsx",
        "sheets": {
            "actividad": "C-94",
            "territorio": "C-96",
            "causas": "C-97",
            "calificacion": "C-98",
            "organizacion": "C-99",
            "tamano": "C-100",
            "duracion": "C-101",
            "cruce": "C-102",
        },
    },
}


REGION_ALIASES = {
    "ANCASH": "ancash",
    "ÁNCASH": "ancash",
    "APURIMAC": "apurimac",
    "APURÍMAC": "apurimac",
    "AREQUIPA": "arequipa",
    "AYACUCHO": "ayacucho",
    "CAJAMARCA": "cajamarca",
    "CALLAO": "callao",
    "CUSCO": "cusco",
    "CUZCO": "cusco",
    "HUANCAVELICA": "huancavelica",
    "HUANUCO": "huanuco",
    "HUÁNUCO": "huanuco",
    "ICA": "ica",
    "JUNIN": "junin",
    "JUNÍN": "junin",
    "LA LIBERTAD": "la_libertad",
    "LAMBAYEQUE": "lambayeque",
    "LIMA": "lima_provincia",
    "LIMA METROPOLITANA": "lima_metropolitana",
    "LIMA PROVINCIA": "lima_provincia",
    "LORETO": "loreto",
    "MOQUEGUA": "moquegua",
    "PASCO": "pasco",
    "PIURA": "piura",
    "PUNO": "puno",
    "SAN MARTIN": "san_martin",
    "SAN MARTÍN": "san_martin",
    "TACNA": "tacna",
    "TUMBES": "tumbes",
    "UCAYALI": "ucayali",
    "OTROS": "otros",
}


IGNORED_CATEGORY_TOKENS = {
    "",
    "TOTAL",
    "ABSOLUTO",
    "%",
}


@dataclass
class ValidationRow:
    anio: int
    modulo: str
    hoja_excel: str
    metrica: str
    total_extraido: float | None
    total_fuente: float | None
    diferencia: float | None
    estado: str


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).replace("\n", " ").replace("\xa0", " ").strip()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def fold_text(value: object) -> str:
    text = normalize_text(value)
    text = "".join(
        ch
        for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    text = text.upper()
    text = text.replace("N°", "NRO")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slug_text(value: object) -> str:
    text = fold_text(value)
    text = re.sub(r"[^A-Z0-9]+", "_", text)
    return text.strip("_").lower()


def as_number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = normalize_text(value)
    if text == "":
        return None
    if text in {"*", "**", "-", "--"}:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def safe_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def extract_tail_notes(df: pd.DataFrame) -> list[str]:
    notes: list[str] = []
    for _, row in df.iterrows():
        text = " ".join(
            normalize_text(value)
            for value in row.tolist()
            if normalize_text(value)
        ).strip()
        if not text:
            continue
        folded = fold_text(text)
        if (
            folded.startswith("FUENTE")
            or folded.startswith("DGT")
            or folded.startswith("ELABORACION")
            or folded.startswith("ELABORADO")
            or folded.startswith("NOTA")
            or folded.startswith("*")
            or "HUELGA FUE REGISTRADA EN LIMA" in folded
            or "HUELGAS REGISTRADAS EN LIMA" in folded
            or "NO SE DISPONE" in folded
            or "HORAS - HOMBRE PERDIDAS GENERADAS" in folded
        ):
            notes.append(text)
    deduped: list[str] = []
    for note in notes:
        if note not in deduped:
            deduped.append(note)
    return deduped


def rule_row(
    anio: int,
    modulo: str,
    categoria_original: str,
    categoria_homologada_fina: str,
    categoria_homologada_agregada: str,
    regla_homologacion: str,
) -> dict[str, object]:
    return {
        "anio": anio,
        "modulo": modulo,
        "categoria_original": categoria_original,
        "categoria_homologada_fina": categoria_homologada_fina,
        "categoria_homologada_agregada": categoria_homologada_agregada,
        "regla_homologacion": regla_homologacion,
    }


def homologate_activity(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "AGRICULTURA" in folded:
        return "agricultura", "agricultura", "agricultura -> agricultura"
    if folded == "PESCA":
        return "pesca", "pesca", "pesca -> pesca"
    if "MINAS Y CANTERAS" in folded:
        return "mineria", "mineria", "minas y canteras -> mineria"
    if "MANUFACTUR" in folded:
        return "manufactura", "manufactura", "manufacturas -> manufactura"
    if "ELECTRICIDAD" in folded or "GAS Y AGUA" in folded:
        return (
            "electricidad_agua",
            "electricidad_agua",
            "electricidad/gas/agua -> electricidad_agua",
        )
    if "CONSTRUCCION" in folded:
        return "construccion", "construccion", "construccion -> construccion"
    if "TRANSPORTE" in folded or "COMUNICACIONES" in folded:
        return "transporte", "transporte", "transporte/comunicaciones -> transporte"
    if "INTERMEDIACION FINANCIERA" in folded or "AFP" in folded:
        return "financiero", "financiero", "intermediacion financiera/AFP -> financiero"
    if "COMERCIO" in folded or "HOTELES Y RESTAURANTES" in folded:
        return "comercio", "comercio", "comercio/hoteles -> comercio"
    if "INMOBILIARI" in folded or "ALQUILER" in folded:
        return "inmobiliario", "inmobiliario", "actividades inmobiliarias/alquiler -> inmobiliario"
    if "ADMINISTRACION PUBLICA" in folded:
        return "adm_publica", "adm_publica", "administracion publica -> adm_publica"
    if "ENSENANZA" in folded:
        return "ensenanza", "ensenanza", "ensenanza -> ensenanza"
    if "SALUD" in folded or "SOCIALES Y DE SALUD" in folded:
        return "salud_social", "salud_social", "servicios sociales y de salud -> salud_social"
    if "OTRAS ACTIV" in folded and ("SERVICIOS" in folded or "SERV." in normalize_text(label) or " SERV " in f" {folded} "):
        return "otros_servicios", "otros_servicios", "otras actividades de servicios -> otros_servicios"
    if "PARO NACIONAL" in folded or folded == "PAROS":
        return "paro_nacional", "paro_nacional", "paro nacional/paros -> paro_nacional"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_calificacion(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "IMPROCEDENTE" in folded or "ILEGALIDAD" in folded or "CON AUTO DE ILEGALIDAD" in folded:
        return "ilegal", "ilegal", "improcedente/ilegalidad -> ilegal"
    if "CONFORMIDAD" in folded or "CONFORME" in folded or "PROCEDENCIA" in folded:
        return "procedente", "procedente", "conforme/procedencia -> procedente"
    if "PROCEDENTE" in folded:
        return "procedente", "procedente", "procedente -> procedente"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_organizacion(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "SINDICATO DE EMPLEADOS" in folded:
        return "sindicato_empleados", "sindicato_empleados", "sindicato de empleados -> sindicato_empleados"
    if "SINDICATO DE OBREROS" in folded:
        return "sindicato_obreros", "sindicato_obreros", "sindicato de obreros -> sindicato_obreros"
    if "SINDICATO UNICO" in folded or "SINDICATO ÚNICO" in normalize_text(label):
        return "sindicato_unico", "sindicato_unico", "sindicato unico -> sindicato_unico"
    if "FEDERACION" in folded:
        return "federacion", "federacion", "federacion(es) -> federacion"
    if "CONFEDERACION" in folded:
        return "confederacion", "confederacion", "confederacion(es) -> confederacion"
    if "DELEGADOS DE EMPLEADOS" in folded:
        return "delegados_empleados", "delegados_empleados", "delegados de empleados -> delegados_empleados"
    if "DELEGADOS DE OBREROS" in folded:
        return "delegados_obreros", "delegados_obreros", "delegados de obreros -> delegados_obreros"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_tamano(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    rules = {
        "20 - 49": ("20_49", "20_49", "20-49 -> 20_49"),
        "50 - 99": ("50_99", "50_99", "50-99 -> 50_99"),
        "100 - 199": ("100_199", "100_199", "100-199 -> 100_199"),
        "200 - 299": ("200_299", "200_299", "200-299 -> 200_299"),
        "300 - 499": ("300_499", "300_mas", "300-499 -> fina 300_499; agregada 300_mas"),
        "500 - 799": ("500_799", "300_mas", "500-799 -> fina 500_799; agregada 300_mas"),
        "800 - 999": ("800_999", "300_mas", "800-999 -> fina 800_999; agregada 300_mas"),
    }
    if folded in rules:
        return rules[folded]
    if "300" in folded and "TRABAJADORES" in folded and ("A MAS" in folded or "A MÁS" in normalize_text(label)):
        return (
            "300_a_mas_trabajadores",
            "300_mas",
            "300 a mas trabajadores -> fina 300_a_mas_trabajadores; agregada 300_mas",
        )
    if "1000" in folded:
        return "1000_mas", "300_mas", "1000+ -> fina 1000_mas; agregada 300_mas"
    if "NO INDICA" in folded:
        return "no_indica", "no_indica", "no indica -> no_indica"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_duracion(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if (
        "DIESISEIS A VEINTIUN" in folded
        or "DIECISEIS A VEINTIUN" in folded
        or "DIESISEIS A VEINTIUN DIAS" in folded
        or "DIECISEIS A VEINTIUN DIAS" in folded
    ):
        return "16_21_dias", "16_mas_dias", "16-21 dias -> fina 16_21_dias; agregada 16_mas_dias"
    if "VEINTIDOS A TRENTICINCO" in folded or "VEINTIDOS A TREINTA Y CINCO" in folded:
        return "22_35_dias", "16_mas_dias", "22-35 dias -> fina 22_35_dias; agregada 16_mas_dias"
    if "TRENTISEIS" in folded or "TREINTA Y SEIS" in folded:
        return "36_mas_dias", "16_mas_dias", "36+ dias -> fina 36_mas_dias; agregada 16_mas_dias"
    if "DIECISEIS DIAS A MAS" in folded or "DIESISEIS DIAS A MAS" in folded:
        return "16_mas_dias", "16_mas_dias", "16 dias a mas -> 16_mas_dias"
    if folded.startswith("UN DIA"):
        return "1_dia", "1_dia", "un dia -> 1_dia"
    if folded.startswith("DOS DIAS"):
        return "2_dias", "2_3_dias", "dos dias -> fina 2_dias; agregada 2_3_dias"
    if folded.startswith("TRES DIAS"):
        return "3_dias", "2_3_dias", "tres dias -> fina 3_dias; agregada 2_3_dias"
    if "CUATRO A SIETE" in folded:
        return "4_7_dias", "4_7_dias", "4-7 dias -> 4_7_dias"
    if "OCHO A QUINCE" in folded:
        return "8_15_dias", "8_15_dias", "8-15 dias -> 8_15_dias"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_causa(label: str) -> tuple[str, str, str]:
    folded = fold_text(label)
    if "PLIEGO" in folded:
        return "pliego_reclamos", "pliego_reclamos", "pliego reclamos -> pliego_reclamos"
    if "OTRAS CAUSAS" in folded:
        return "otras_causas", "otras_causas", "otras causas -> otras_causas"
    return slug_text(label), slug_text(label), "sin traduccion adicional; se normaliza el texto"


def homologate_territorio(label: str, parent_region_slug: str | None) -> tuple[str, str, str, str, str]:
    original = normalize_text(label)
    starred = original.endswith("*")
    clean = original.rstrip("*").strip()
    folded = fold_text(clean)
    if folded == "LIMA SEDE CENTRAL":
        rule = "LIMA SEDE CENTRAL -> zona historica; fina=lima_sede_central; agregada=lima_metropolitana; region_madre=lima_metropolitana"
        if starred:
            rule += "; marca de paro nacional registrado en Lima Metropolitana"
        return "lima_sede_central", "lima_metropolitana", "zona", "lima_metropolitana", rule
    if folded in REGION_ALIASES:
        region_slug = REGION_ALIASES[folded]
        if parent_region_slug == region_slug:
            rule = f"{clean} -> zona con mismo nombre que la region; region_madre={region_slug}"
            if starred:
                rule += "; marca de paro nacional registrado en Lima Metropolitana"
            return region_slug, region_slug, "zona", region_slug, rule
        rule = f"{clean} -> region homologada {region_slug}"
        if starred:
            rule += "; marca de paro nacional registrado en Lima Metropolitana"
        return region_slug, region_slug, "regional", region_slug, rule
    zona_slug = slug_text(clean)
    parent_slug = parent_region_slug or "sin_region_padre"
    rule = f"{clean} -> zona; region_madre={parent_slug}"
    if starred:
        rule += "; marca de paro nacional registrado en Lima Metropolitana"
    return zona_slug, zona_slug, "zona", parent_slug, rule


def generic_rows(
    df: pd.DataFrame,
    category_col: int,
    huelgas_col: int,
    trabajadores_col: int,
    horas_col: int,
    pct_huelgas_col: int | None = None,
    pct_trabajadores_col: int | None = None,
    pct_horas_col: int | None = None,
) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    rows: list[dict[str, object]] = []
    totals = {
        "huelgas": None,
        "trabajadores_comprendidos": None,
        "horas_hombre_perdidas": None,
    }
    for _, row in df.iterrows():
        category = normalize_text(row.iloc[category_col] if category_col < len(row) else None)
        if not category:
            continue
        folded = fold_text(category)
        if any(token in folded for token in ["CUADRO", "PERU", "SECTOR PRIVADO"]):
            continue
        huelgas = as_number(row.iloc[huelgas_col] if huelgas_col < len(row) else None)
        trabajadores = as_number(row.iloc[trabajadores_col] if trabajadores_col < len(row) else None)
        horas = as_number(row.iloc[horas_col] if horas_col < len(row) else None)
        if folded == "TOTAL":
            totals["huelgas"] = huelgas
            totals["trabajadores_comprendidos"] = trabajadores
            totals["horas_hombre_perdidas"] = horas
            continue
        if huelgas is None and trabajadores is None and horas is None:
            continue
        rows.append(
            {
                "categoria_original": category,
                "huelgas": huelgas,
                "pct_huelgas": as_number(row.iloc[pct_huelgas_col]) if pct_huelgas_col is not None else None,
                "trabajadores_comprendidos": trabajadores,
                "pct_trabajadores": as_number(row.iloc[pct_trabajadores_col])
                if pct_trabajadores_col is not None
                else None,
                "horas_hombre_perdidas": horas,
                "pct_horas": as_number(row.iloc[pct_horas_col]) if pct_horas_col is not None else None,
            }
        )
    return rows, totals


def activity_rows(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    header_row = df.iloc[5]
    workers_header_col = next(
        idx
        for idx, value in enumerate(header_row.tolist())
        if "TRABAJADORES COMPRENDIDOS" in fold_text(value)
    )
    hours_header_col = next(
        idx
        for idx, value in enumerate(header_row.tolist())
        if "HORAS - HOMBRE PERDIDAS" in fold_text(value)
    )
    if workers_header_col == 4:
        return generic_rows(df, 1, 2, 4, 6, 3, 5, 7)
    return generic_rows(df, 1, 2, 6, 10, 4, 8, 12)


def causes_rows(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    total_idx = None
    for idx, row in df.iterrows():
        if fold_text(row.iloc[1] if len(row) > 1 else None) == "TOTAL":
            total_idx = idx
            break
    if total_idx is None:
        raise ValueError("No se encontró la fila TOTAL en causas")
    row = df.iloc[total_idx]
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


def territory_rows(df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, float | None]]:
    return generic_rows(df, 1, 2, 4, 6)


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
            for nivel in ["regional", "zona"]:
                level_sum = pd.to_numeric(
                    df.loc[df["nivel_territorial"] == nivel, metric],
                    errors="coerce",
                ).sum(min_count=1)
                level_value = None if pd.isna(level_sum) else float(level_sum)
                diff = safe_diff(level_value, source_value)
                state = "ok" if diff is not None and abs(diff) <= 0.01 else "revisar"
                validations.append(
                    ValidationRow(
                        anio=anio,
                        modulo=modulo,
                        hoja_excel=hoja_excel,
                        metrica=f"{metric}_{nivel}",
                        total_extraido=level_value,
                        total_fuente=source_value,
                        diferencia=diff,
                        estado=state,
                    )
                )
        return validations

    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        extracted = pd.to_numeric(df[metric], errors="coerce").sum(min_count=1)
        extracted_value = None if pd.isna(extracted) else float(extracted)
        source_value = totals.get(metric)
        diff = safe_diff(extracted_value, source_value)
        state = "ok"
        if extracted_value is None and source_value is None:
            state = "sin_dato"
        elif diff is None:
            state = "revisar"
        elif abs(diff) > 0.01:
            state = "revisar"
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


def build_module_frame(
    anio: int,
    modulo: str,
    hoja_excel: str,
    df_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, list[ValidationRow], list[str]]:
    notes = extract_tail_notes(df_raw)
    rules: list[dict[str, object]] = []

    if modulo == "actividad":
        rows, totals = activity_rows(df_raw)
    elif modulo == "calificacion":
        rows, totals = generic_rows(df_raw, 1, 2, 4, 6)
    elif modulo == "organizacion":
        rows, totals = generic_rows(df_raw, 1, 2, 6, 10, 4, 8, 12)
    elif modulo == "tamano":
        rows, totals = generic_rows(df_raw, 1, 2, 6, 10, 4, 8, 12)
    elif modulo == "duracion":
        rows, totals = generic_rows(df_raw, 1, 2, 6, 10, 4, 8, 12)
    elif modulo == "causas":
        rows, totals = causes_rows(df_raw)
    elif modulo == "territorio":
        rows, totals = territory_rows(df_raw)
    else:
        raise ValueError(f"Módulo no soportado: {modulo}")

    current_region_slug: str | None = None
    output_rows: list[dict[str, object]] = []
    for row in rows:
        original = normalize_text(row["categoria_original"])
        flag_hhp_arrastre = int(
            any("HORAS - HOMBRE PERDIDAS GENERADAS" in fold_text(note) for note in notes)
        )
        flag_faltante_fuente = int(
            any("NO SE DISPONE" in fold_text(note) for note in notes)
            or any(value is None for key, value in row.items() if key in {"trabajadores_comprendidos", "horas_hombre_perdidas"})
        )
        if modulo == "territorio":
            flag_paro_nacional_lima = int(
                original.endswith("*") or "LIMA METROPOLITANA" in fold_text(original)
            )
        else:
            flag_paro_nacional_lima = int("PARO NACIONAL" in fold_text(original))

        nivel_territorial = None
        territorio_padre = None
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
        elif modulo == "territorio":
            fina, agregada, nivel_territorial, territorio_padre, regla = homologate_territorio(
                original,
                current_region_slug,
            )
            if nivel_territorial == "regional":
                current_region_slug = fina
        else:
            fina = agregada = slug_text(original)
            regla = "sin homologacion"

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
                "nivel_territorial": nivel_territorial,
                "territorio_padre": territorio_padre,
                "huelgas": row.get("huelgas"),
                "pct_huelgas": row.get("pct_huelgas"),
                "trabajadores_comprendidos": row.get("trabajadores_comprendidos"),
                "pct_trabajadores": row.get("pct_trabajadores"),
                "horas_hombre_perdidas": row.get("horas_hombre_perdidas"),
                "pct_horas": row.get("pct_horas"),
                "flag_hhp_arrastre": flag_hhp_arrastre,
                "flag_faltante_fuente": flag_faltante_fuente,
                "flag_paro_nacional_registrado_lima": flag_paro_nacional_lima,
                "nota_fuente": " | ".join(notes),
            }
        )

    module_df = pd.DataFrame(output_rows)
    rules_df = pd.DataFrame(rules).drop_duplicates()
    validations = validate_module(anio, modulo, hoja_excel, module_df, totals)
    return module_df, rules_df, validations, notes


def process_year(anio: int, config: dict[str, object]) -> None:
    path: Path = config["path"]
    sheets: dict[str, str] = config["sheets"]
    excel_path = OUTPUT_DIR / f"huelgas_{anio}_homologado.xlsx"

    module_frames: dict[str, pd.DataFrame] = {}
    rules_frames: list[pd.DataFrame] = []
    validation_rows: list[ValidationRow] = []
    notes_rows: list[dict[str, object]] = []

    for modulo in ["actividad", "territorio", "causas", "calificacion", "organizacion", "tamano", "duracion"]:
        hoja = sheets[modulo]
        df_raw = pd.read_excel(path, sheet_name=hoja, header=None)
        module_df, rules_df, validations, notes = build_module_frame(anio, modulo, hoja, df_raw)
        module_frames[modulo] = module_df
        rules_frames.append(rules_df)
        validation_rows.extend(validations)
        for note in notes:
            notes_rows.append(
                {
                    "anio": anio,
                    "modulo": modulo,
                    "hoja_excel": hoja,
                    "nota_fuente": note,
                }
            )

    validation_df = pd.DataFrame([row.__dict__ for row in validation_rows])
    notes_df = pd.DataFrame(notes_rows).drop_duplicates()
    dictionary_df = pd.concat(rules_frames, ignore_index=True).drop_duplicates()
    summary_df = pd.DataFrame(
        [
            {
                "anio": anio,
                "archivo_fuente": str(path.relative_to(ROOT)),
                "archivo_salida": str(excel_path.relative_to(ROOT)),
                "modulos_generados": len(module_frames),
                "filas_totales": sum(len(df) for df in module_frames.values()),
                "validaciones_revisar": int((validation_df["estado"] == "revisar").sum()),
                "notas_fuente": len(notes_df),
            }
        ]
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen", index=False)
        for modulo, df in module_frames.items():
            df.to_excel(writer, sheet_name=modulo, index=False)
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
