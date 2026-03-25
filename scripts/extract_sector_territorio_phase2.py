from __future__ import annotations

from pathlib import Path

import pandas as pd

from extract_era2_huelgas_2000_2003 import YEAR_CONFIG as YEAR_CONFIG_2000_2003
from extract_era2_huelgas_2004_2020 import YEAR_CONFIG as YEAR_CONFIG_2004_2020
from extract_era3_huelgas import (
    YEAR_CONFIG as YEAR_CONFIG_2021_2024,
    REGION_ALIASES,
    ROOT,
    as_number,
    extract_tail_notes,
    fold_text,
    homologate_activity,
    homologate_territorio,
    normalize_text,
    safe_diff,
    slug_text,
)


OUTPUT_DIR = ROOT / "bases" / "cruce_sector_territorio"
YEARS_ALL = list(range(1993, 2025))


def cross_year_config() -> dict[int, dict[str, object]]:
    config: dict[int, dict[str, object]] = {}
    for year in [2001, 2002, 2003]:
        config[year] = {
            "path": YEAR_CONFIG_2000_2003[year]["path"],
            "sheet": "C-11",
            "nota": "Cuadro cruzado actividad x territorio disponible en C-11.",
        }
    for year, path in YEAR_CONFIG_2004_2020.items():
        config[year] = {
            "path": path,
            "sheet": "C-11",
            "nota": "Cuadro cruzado actividad x territorio disponible en C-11.",
        }
    for year, cfg in YEAR_CONFIG_2021_2024.items():
        config[year] = {
            "path": cfg["path"],
            "sheet": cfg["sheets"]["cruce"],
            "nota": f"Cuadro cruzado actividad x territorio disponible en {cfg['sheets']['cruce']}.",
        }
    return config


def detect_header_row(df: pd.DataFrame) -> int:
    candidates: list[int] = []
    max_row = min(35, len(df))
    for idx in range(max_row):
        current = " ".join(
            normalize_text(value) for value in df.iloc[idx].tolist() if normalize_text(value)
        )
        future = " ".join(
            normalize_text(value)
            for row_idx in range(idx, min(idx + 4, len(df)))
            for value in df.iloc[row_idx].tolist()
            if normalize_text(value)
        )
        current_folded = fold_text(current)
        future_folded = fold_text(future)
        if (
            any(token in future_folded for token in ["DIRECCIONES", "DIRECCION", "GERENCIA REGIONAL", "ZONAS DE TRABAJO"])
            and "TOTAL" in future_folded
            and (
                "DIRECCIONES" in current_folded
                or "DIRECCION" in current_folded
                or "REGIONALES" in current_folded
                or "ZONAS DE TRABAJO" in current_folded
            )
        ):
            candidates.append(idx)
    if candidates:
        return min(candidates)
    raise ValueError("No se encontró la fila de encabezado del cuadro cruzado")


def detect_structure(df: pd.DataFrame, header_row: int) -> tuple[int, list[tuple[int, str]], int | None]:
    combined: dict[int, str] = {}
    max_header_row = min(header_row + 3, len(df) - 1)
    for col in range(len(df.columns)):
        parts = [
            normalize_text(df.iat[row_idx, col])
            for row_idx in range(header_row, max_header_row + 1)
            if col < len(df.columns)
        ]
        text = " ".join(part for part in parts if part).strip()
        if text:
            combined[col] = text

    label_col = min(
        col
        for col, text in combined.items()
        if any(token in fold_text(text) for token in ["DIRECCIONES", "DIRECCION", "ZONAS", "TRABAJO"])
    )

    activity_cols: list[tuple[int, str]] = []
    total_col: int | None = None
    activity_tokens = [
        "AGRICULTURA",
        "MINAS",
        "MANUFACTUR",
        "MANU",
        "ELECTRICIDAD",
        "CONSTRUCCION",
        "CONSTRU",
        "COMERCIO",
        "TRANSPORTE",
        "INTERMEDIACION",
        "INMOBILIARI",
        "ALQUILER",
        "ADMINISTRA",
        "ENSENANZA",
        "SERVICIOS",
        "COMUNITARIOS",
        "OTRAS ACTIV",
        "PARO NACIONAL",
        "HOTELES",
        "RESTAURAMTES",
    ]
    for col, text in sorted(combined.items()):
        if col <= label_col:
            continue
        folded = fold_text(text)
        if not folded:
            continue
        if "%" in text or folded == "%":
            continue
        if ("TOTAL" in folded or "ABSOLUTO" in folded) and not any(
            token in folded for token in activity_tokens
        ):
            if total_col is None:
                total_col = col
            continue
        if any(token in folded for token in activity_tokens):
            activity_cols.append((col, text))
            continue
        if any(token in folded for token in ["ACTIVIDAD ECONOMICA", "DIRECCIONES", "DIRECCION", "ZONAS", "TRABAJO"]):
            continue
    return label_col, activity_cols, total_col


def first_label(row: pd.Series, label_col: int) -> str:
    probe_cols = list(range(0, min(label_col + 2, len(row))))
    for col in probe_cols:
        text = normalize_text(row.iloc[col])
        if text:
            return text
    return ""


def metric_name(label: str) -> str | None:
    folded = fold_text(label)
    if "TRABAJADORES COMPRENDIDOS" in folded or "NO.T/C" in folded:
        return "trabajadores_comprendidos"
    if "HORAS-HOMBRE PERDIDAS" in folded or "HORAS - HOMBRE PERDIDAS" in folded or "NO. H/HP" in folded:
        return "horas_hombre_perdidas"
    if folded == "HUELGAS" or "NO. H." in folded:
        return "huelgas"
    return None


def territory_homologation(
    year: int,
    original: str,
    current_region_slug: str | None,
) -> tuple[str, str, str, str | None, str, str | None]:
    clean = normalize_text(original).rstrip("*").strip()
    folded = fold_text(clean)
    if year >= 2014:
        fina, agregada, nivel, parent, regla = homologate_territorio(clean, current_region_slug)
        next_region = agregada if nivel == "regional" else current_region_slug
        return fina, agregada, nivel, parent, regla, next_region
    if folded in REGION_ALIASES:
        region_slug = REGION_ALIASES[folded]
        return (
            region_slug,
            region_slug,
            "regional",
            region_slug,
            f"{clean} -> region homologada {region_slug} en cuadro cruzado antiguo",
            region_slug,
        )
    zona_slug = slug_text(clean)
    return (
        zona_slug,
        zona_slug,
        "zona",
        None,
        f"{clean} -> zona en cuadro cruzado antiguo; sin region_padre inferida automaticamente",
        current_region_slug,
    )


def emit_block(
    year: int,
    sheet_name: str,
    territory_original: str,
    territory_meta: tuple[str, str, str, str | None, str],
    activity_cols: list[tuple[int, str]],
    metrics: dict[str, dict[int, float | None]],
    totals: dict[str, float | None],
    note: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    territory_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    territorio_fina, territorio_agregada, nivel, parent, regla_territorio = territory_meta

    for activity_col, activity_original in activity_cols:
        actividad_fina, actividad_agregada, regla_actividad = homologate_activity(activity_original)
        huelgas = metrics.get("huelgas", {}).get(activity_col)
        trabajadores = metrics.get("trabajadores_comprendidos", {}).get(activity_col)
        horas = metrics.get("horas_hombre_perdidas", {}).get(activity_col)
        if huelgas is None and trabajadores is None and horas is None:
            continue
        territory_rows.append(
            {
                "anio": year,
                "hoja_excel": sheet_name,
                "territorio_original": territory_original,
                "territorio_homologado_fino": territorio_fina,
                "territorio_homologado_agregado": territorio_agregada,
                "nivel_territorial": nivel,
                "territorio_padre": parent,
                "regla_territorio": regla_territorio,
                "actividad_original": activity_original,
                "actividad_homologada_fina": actividad_fina,
                "actividad_homologada_agregada": actividad_agregada,
                "regla_actividad": regla_actividad,
                "huelgas": huelgas,
                "trabajadores_comprendidos": trabajadores,
                "horas_hombre_perdidas": horas,
                "total_territorio_huelgas": totals.get("huelgas"),
                "total_territorio_trabajadores": totals.get("trabajadores_comprendidos"),
                "total_territorio_horas": totals.get("horas_hombre_perdidas"),
                "nota_fuente": note,
            }
        )

    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        total_extraido = sum(
            value for value in metrics.get(metric, {}).values() if value is not None
        )
        total_fuente = totals.get(metric)
        diff = safe_diff(total_extraido, total_fuente)
        validation_rows.append(
            {
                "anio": year,
                "hoja_excel": sheet_name,
                "territorio_original": territory_original,
                "territorio_homologado_agregado": territorio_agregada,
                "nivel_territorial": nivel,
                "metrica": metric,
                "total_extraido": total_extraido,
                "total_fuente": total_fuente,
                "diferencia": diff,
                "estado": "sin_total" if total_fuente is None else ("ok" if diff in {0, 0.0} else "revisar"),
            }
        )
    return territory_rows, validation_rows


def parse_cross_table(
    year: int,
    path: Path,
    sheet_name: str,
    note: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    df = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_row = detect_header_row(df)
    label_col, activity_cols, total_col = detect_structure(df, header_row)
    notes = extract_tail_notes(df)

    rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    current_territory: str | None = None
    current_region_slug: str | None = None
    current_meta: tuple[str, str, str, str | None, str] | None = None
    metrics: dict[str, dict[int, float | None]] = {}
    totals: dict[str, float | None] = {}

    for idx in range(header_row + 1, len(df)):
        row = df.iloc[idx]
        label = first_label(row, label_col)
        if not label:
            continue
        folded = fold_text(label)
        if folded in {"TOTAL", "ABSOLUTO", "%"}:
            continue
        if any(
            token in folded
            for token in ["FUENTE", "ELABORADO", "ELABORACION", "ELABORACIÓN", "NOTA", "DGT", "CONCLUSION", "CONCLUSIÓN"]
        ):
            continue
        if folded in {"PERU", "NIVEL NACIONAL"}:
            continue

        metric = metric_name(label)
        if metric is None:
            if current_territory and metrics and current_meta is not None:
                block_rows, block_validation = emit_block(
                    year=year,
                    sheet_name=sheet_name,
                    territory_original=current_territory,
                    territory_meta=current_meta,
                    activity_cols=activity_cols,
                    metrics=metrics,
                    totals=totals,
                    note=note,
                )
                rows.extend(block_rows)
                validation_rows.extend(block_validation)
                metrics = {}
                totals = {}

            current_territory = label
            fina, agregada, nivel, parent, regla, next_region = territory_homologation(
                year, label, current_region_slug
            )
            current_meta = (fina, agregada, nivel, parent, regla)
            current_region_slug = next_region
            continue

        if current_territory is None:
            continue

        metrics[metric] = {
            col: as_number(row.iloc[col]) if col < len(row) else None for col, _ in activity_cols
        }
        totals[metric] = as_number(row.iloc[total_col]) if total_col is not None else None

    if current_territory and metrics and current_meta is not None:
        block_rows, block_validation = emit_block(
            year=year,
            sheet_name=sheet_name,
            territory_original=current_territory,
            territory_meta=current_meta,
            activity_cols=activity_cols,
            metrics=metrics,
            totals=totals,
            note=note,
        )
        rows.extend(block_rows)
        validation_rows.extend(block_validation)

    return rows, validation_rows, notes


def write_note(coverage: pd.DataFrame) -> None:
    available = coverage.loc[coverage["estado_cruce"] == "disponible", "anio"].tolist()
    unavailable = coverage.loc[coverage["estado_cruce"] != "disponible", ["anio", "estado_cruce", "detalle"]]
    lines = [
        "# Nota metodologica: cruce sector x territorio",
        "",
        "Se extrajo una base complementaria del cuadro `actividad x territorio` para los años donde ese cuadro existe y fue legible con un parser reproducible.",
        "",
        f"- anos disponibles en esta fase: {available[0]}-{available[-1]}",
        "- la base resultante no reemplaza la base maestra principal; la complementa",
        "- en `2001-2013` varias zonas quedan sin `territorio_padre` inferido automaticamente para evitar asignaciones territoriales equivocadas en los layouts antiguos",
        "- en `2014-2024` se aprovecha mejor la jerarquia region/zona del cuadro",
        "",
        "## Años sin cuadro cruzado disponible en esta fase",
        "",
    ]
    for _, row in unavailable.iterrows():
        lines.append(f"- `{int(row['anio'])}`: {row['estado_cruce']} ({row['detalle']})")
    lines.append("")
    lines.append("## Validacion")
    lines.append("")
    lines.append("Para cada territorio se verifico, por metrica, que la suma de sectores coincida con el total absoluto del mismo cuadro.")
    lines.append("La validacion se guarda en `validacion_sector_territorio_2001_2024.csv`.")
    (OUTPUT_DIR / "nota_metodologica.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = cross_year_config()

    coverage_rows: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    all_validation: list[dict[str, object]] = []

    for year in YEARS_ALL:
        if year not in config:
            coverage_rows.append(
                {
                    "anio": year,
                    "estado_cruce": "no_disponible",
                    "detalle": "No existe cuadro cruzado utilizable en el pipeline actual.",
                }
            )
            continue

        year_cfg = config[year]
        path = year_cfg["path"]
        sheet_name = year_cfg["sheet"]
        note = year_cfg["nota"]
        rows, validations, notes = parse_cross_table(year, path, sheet_name, note)
        all_rows.extend(rows)
        all_validation.extend(validations)
        coverage_rows.append(
            {
                "anio": year,
                "estado_cruce": "disponible",
                "detalle": f"{sheet_name} | {' | '.join(notes[:2])}" if notes else sheet_name,
            }
        )

    cross_df = pd.DataFrame(all_rows)
    validation_df = pd.DataFrame(all_validation)
    coverage_df = pd.DataFrame(coverage_rows)

    cross_df.to_csv(
        OUTPUT_DIR / "sector_territorio_2001_2024.csv",
        index=False,
        encoding="utf-8-sig",
    )
    validation_df.to_csv(
        OUTPUT_DIR / "validacion_sector_territorio_2001_2024.csv",
        index=False,
        encoding="utf-8-sig",
    )
    coverage_df.to_csv(
        OUTPUT_DIR / "cobertura_sector_territorio_1993_2024.csv",
        index=False,
        encoding="utf-8-sig",
    )

    if not validation_df.empty:
        summary_rows: list[dict[str, object]] = []
        for (year, metric), group in validation_df.groupby(["anio", "metrica"], dropna=False):
            states = set(group["estado"].dropna().astype(str))
            if "revisar" in states:
                status = "revisar"
            elif states == {"sin_total"}:
                status = "ok_con_salvedad"
            elif "sin_total" in states:
                status = "ok_con_salvedad"
            else:
                status = "ok"
            summary_rows.append(
                {
                    "anio": year,
                    "metrica": metric,
                    "estado": status,
                    "filas_ok": int(group["estado"].eq("ok").sum()),
                    "filas_sin_total": int(group["estado"].eq("sin_total").sum()),
                    "filas_revisar": int(group["estado"].eq("revisar").sum()),
                }
            )
        summary = pd.DataFrame(summary_rows)
        summary.to_csv(
            OUTPUT_DIR / "validacion_sector_territorio_resumen.csv",
            index=False,
            encoding="utf-8-sig",
        )

    write_note(coverage_df)


if __name__ == "__main__":
    main()
