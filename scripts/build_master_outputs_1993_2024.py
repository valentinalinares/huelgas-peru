from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASES_DIR = ROOT / "bases"
OUTPUT_DIR = BASES_DIR / "maestra"
GRAPH_DIR = OUTPUT_DIR / "graficos"
NOTEBOOK_DIR = ROOT / "notebooks"

BLOCK_DIRS = [
    "era1_homologados",
    "era2_homologados_1996_1999",
    "era2_homologados_2000_2003",
    "era2_homologados_2004_2020",
    "era3_homologados",
]
MODULES = [
    "actividad",
    "territorio",
    "causas",
    "calificacion",
    "organizacion",
    "tamano",
    "duracion",
]
MODULE_CONCEPTS = {
    "actividad": "Rama o sector economico reportado por el anuario para clasificar las huelgas.",
    "territorio": "Ubicacion territorial reportada por la fuente para clasificar las huelgas.",
    "causas": "Motivo resumido de la huelga segun el cuadro anual de causas.",
    "calificacion": "Condicion legal de la huelga segun la categoria juridica usada en cada anuario.",
    "organizacion": "Tipo de organizacion sindical o representacion que convoca o sostiene la huelga.",
    "tamano": "Tramo de trabajadores comprendidos por huelga segun el cuadro de tamano.",
    "duracion": "Tramo de duracion de la huelga segun el cuadro anual de dias.",
}
MODULE_NOTES = {
    "actividad": (
        "La fuente cambia de nomenclatura sectorial entre años. "
        "Se preserva la categoria original y se homologan sectores comparables. "
        "No se elimina `adm_publica`: se conserva porque la fuente la reporta explicitamente."
    ),
    "territorio": (
        "La fuente mezcla nivel regional y zona. "
        "La comparabilidad requiere distinguir `nivel_territorial` y no sumar region + zona."
    ),
    "causas": "La serie comparable se concentra en `pliego_reclamos` y `otras_causas`.",
    "calificacion": (
        "La terminologia juridica cambia entre años, pero la agregacion comparable es `procedente` e `ilegal`."
    ),
    "organizacion": (
        "La fuente distingue sindicatos, delegados, federaciones y confederaciones, con variantes historicas."
    ),
    "tamano": (
        "Los tramos altos se subdividen desde 2014; para comparabilidad longitudinal se agregan en `300_mas`."
    ),
    "duracion": (
        "El tramo largo se subdivide desde 2012; para comparabilidad longitudinal se agrega en `16_mas_dias`."
    ),
}
MASTER_COLUMNS = [
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
    "archivo_homologado",
    "carpeta_bloque",
    "tipo_anio",
]


def workbook_paths() -> list[tuple[int, str, Path]]:
    rows: list[tuple[int, str, Path]] = []
    for block in BLOCK_DIRS:
        for path in sorted((BASES_DIR / block).glob("huelgas_*_homologado.xlsx")):
            match = re.search(r"huelgas_(\d{4})_homologado\.xlsx$", path.name)
            if match:
                rows.append((int(match.group(1)), block, path))
    return sorted(rows, key=lambda item: item[0])


def collect_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master_frames: list[pd.DataFrame] = []
    coverage_rows: list[dict[str, object]] = []
    validation_frames: list[pd.DataFrame] = []
    annual_summary_rows: list[dict[str, object]] = []

    for year, block, path in workbook_paths():
        xls = pd.ExcelFile(path)
        resumen = pd.read_excel(path, sheet_name="resumen")
        tipo_anio = (
            resumen["tipo_anio"].iloc[0]
            if "tipo_anio" in resumen.columns and not resumen.empty
            else "completo"
        )

        validation = pd.read_excel(path, sheet_name="validacion")
        validation["archivo_homologado"] = path.name
        validation["carpeta_bloque"] = block
        validation_frames.append(validation)

        annual_summary_rows.append(
            {
                "anio": year,
                "archivo_homologado": path.name,
                "carpeta_bloque": block,
                "tipo_anio": tipo_anio,
                "hojas_presentes": ", ".join(xls.sheet_names),
                "validaciones_revisar": int(validation["estado"].eq("revisar").sum()),
            }
        )

        for modulo in MODULES:
            module_df = pd.read_excel(path, sheet_name=modulo)
            module_df["archivo_homologado"] = path.name
            module_df["carpeta_bloque"] = block
            module_df["tipo_anio"] = tipo_anio
            master_frames.append(module_df)

            estados = sorted(
                validation.loc[validation["modulo"] == modulo, "estado"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            coverage_rows.append(
                {
                    "anio": year,
                    "archivo_homologado": path.name,
                    "carpeta_bloque": block,
                    "tipo_anio": tipo_anio,
                    "modulo": modulo,
                    "filas_modulo": len(module_df),
                    "modulo_con_datos": int(len(module_df) > 0),
                    "estados_validacion": ", ".join(estados),
                    "modulo_no_disponible_fuente": int("no_disponible" in estados),
                }
            )

    master_df = pd.concat(master_frames, ignore_index=True)
    master_df = master_df[MASTER_COLUMNS].sort_values(
        ["anio", "modulo", "categoria_homologada_agregada", "categoria_original"],
        na_position="last",
    )
    coverage_df = pd.DataFrame(coverage_rows).sort_values(["anio", "modulo"])
    validation_df = pd.concat(validation_frames, ignore_index=True).sort_values(
        ["anio", "modulo", "metrica"]
    )
    annual_summary_df = pd.DataFrame(annual_summary_rows).sort_values("anio")
    return master_df, coverage_df, validation_df, annual_summary_df


def build_legalidad(master_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    legalidad = master_df[
        (master_df["modulo"] == "calificacion")
        & master_df["categoria_homologada_agregada"].isin(["procedente", "ilegal"])
        & master_df["huelgas"].notna()
    ].copy()
    legalidad = legalidad.sort_values(["anio", "categoria_homologada_agregada"])

    resumen = (
        legalidad.groupby(["anio", "categoria_homologada_agregada"], as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .pivot(index="anio", columns="categoria_homologada_agregada")
    )
    resumen.columns = [f"{metric}_{cat}" for metric, cat in resumen.columns]
    resumen = resumen.reset_index().sort_values("anio")
    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        proc = f"{metric}_procedente"
        ilegal = f"{metric}_ilegal"
        if proc in resumen.columns and ilegal in resumen.columns:
            resumen[f"{metric}_total_observado"] = resumen[[proc, ilegal]].sum(axis=1)
    return legalidad, resumen


def build_calificacion_verification(validation_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    verif = validation_df[validation_df["modulo"] == "calificacion"].copy()
    verif = verif.sort_values(["anio", "metrica"])
    resumen = (
        verif.pivot_table(
            index=["anio", "archivo_homologado", "carpeta_bloque"],
            columns="metrica",
            values="estado",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    for metric in ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]:
        if metric not in resumen.columns:
            resumen[metric] = None
    resumen["resultado_general"] = resumen[
        ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
    ].apply(
        lambda row: (
            "ok"
            if set(row.dropna().astype(str)) == {"ok"}
            else (
                "no_disponible"
                if "no_disponible" in set(row.dropna().astype(str))
                else "mixto"
            )
        ),
        axis=1,
    )
    resumen = resumen.sort_values("anio")
    return verif, resumen


def build_year_sector(master_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = master_df[
        (master_df["modulo"] == "actividad") & master_df["huelgas"].notna()
    ].copy()
    data = (
        data.groupby(["anio", "categoria_homologada_agregada"], as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .sort_values(["anio", "categoria_homologada_agregada"])
    )
    pivot = (
        data.pivot(index="anio", columns="categoria_homologada_agregada", values="huelgas")
        .fillna(0)
        .sort_index()
    )
    return data, pivot.reset_index()


def build_year_territory(master_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = master_df[
        (master_df["modulo"] == "territorio")
        & (master_df["nivel_territorial"] == "regional")
        & master_df["huelgas"].notna()
    ].copy()
    data = (
        data.groupby(["anio", "categoria_homologada_agregada"], as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .sort_values(["anio", "categoria_homologada_agregada"])
    )
    pivot = (
        data.pivot(index="anio", columns="categoria_homologada_agregada", values="huelgas")
        .fillna(0)
        .sort_index()
    )
    return data, pivot.reset_index()


def build_common_language_reference(
    master_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    reference = master_df.copy()
    reference = reference[
        reference["categoria_homologada_agregada"].notna()
        & reference["categoria_homologada_agregada"].astype(str).ne("")
    ].copy()
    reference["nivel_territorial"] = reference["nivel_territorial"].fillna("")
    reference["regla_homologacion"] = reference["regla_homologacion"].fillna("")
    reference["categoria_homologada_fina"] = reference["categoria_homologada_fina"].fillna("")

    detail = (
        reference.groupby(
            [
                "modulo",
                "categoria_homologada_agregada",
                "categoria_homologada_fina",
                "regla_homologacion",
                "nivel_territorial",
            ],
            as_index=False,
        )
        .agg(
            anio_min=("anio", "min"),
            anio_max=("anio", "max"),
            n_anios=("anio", "nunique"),
        )
        .sort_values(
            [
                "modulo",
                "categoria_homologada_agregada",
                "categoria_homologada_fina",
                "nivel_territorial",
                "regla_homologacion",
            ]
        )
    )

    summary_rows: list[dict[str, object]] = []
    category_rows: list[dict[str, object]] = []
    for modulo in MODULES:
        sub = detail[detail["modulo"] == modulo].copy()
        agregadas = sorted(
            x for x in sub["categoria_homologada_agregada"].dropna().astype(str).unique().tolist() if x
        )
        finas = sorted(
            x for x in sub["categoria_homologada_fina"].dropna().astype(str).unique().tolist() if x
        )
        reglas = sorted(
            x for x in sub["regla_homologacion"].dropna().astype(str).unique().tolist() if x
        )
        summary_rows.append(
            {
                "modulo": modulo,
                "concepto": MODULE_CONCEPTS.get(modulo, ""),
                "observacion_metodologica": MODULE_NOTES.get(modulo, ""),
                "n_categorias_agregadas": len(agregadas),
                "categorias_agregadas": " | ".join(agregadas),
                "n_categorias_finas": len(finas),
                "categorias_finas": " | ".join(finas),
                "n_reglas_homologacion": len(reglas),
            }
        )
        grouped_categories = (
            sub.groupby(["categoria_homologada_agregada", "nivel_territorial"], as_index=False)
            .agg(
                anio_min=("anio_min", "min"),
                anio_max=("anio_max", "max"),
                n_anios=("n_anios", "max"),
            )
            .sort_values(["categoria_homologada_agregada", "nivel_territorial"])
        )
        for _, row in grouped_categories.iterrows():
            category_rows.append(
                {
                    "modulo": modulo,
                    "concepto": MODULE_CONCEPTS.get(modulo, ""),
                    "categoria_homologada_agregada": row["categoria_homologada_agregada"],
                    "nivel_territorial": row["nivel_territorial"],
                    "anio_min": row["anio_min"],
                    "anio_max": row["anio_max"],
                    "n_anios_observados": row["n_anios"],
                    "observacion_metodologica": MODULE_NOTES.get(modulo, ""),
                }
            )
    summary = pd.DataFrame(summary_rows)
    categories = pd.DataFrame(category_rows)
    return detail, summary, categories


def save_heatmap(df: pd.DataFrame, title: str, output_path: Path, top_n: int | None = None) -> None:
    heat = df.set_index(df.columns[0])
    if top_n is not None and heat.shape[1] > top_n:
        top_cols = heat.sum(axis=0).sort_values(ascending=False).head(top_n).index
        heat = heat[top_cols]
    fig_w = max(10, heat.shape[1] * 0.5)
    fig_h = max(6, heat.shape[0] * 0.25)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(heat.values, aspect="auto", cmap="YlOrRd")
    ax.set_title(title)
    ax.set_xticks(range(heat.shape[1]))
    ax.set_xticklabels(heat.columns, rotation=90, fontsize=8)
    ax.set_yticks(range(heat.shape[0]))
    ax.set_yticklabels(heat.index.astype(str), fontsize=8)
    fig.colorbar(im, ax=ax, label="Huelgas")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_legalidad_plots(legalidad_resumen: pd.DataFrame) -> None:
    for metric, filename, title in [
        ("huelgas", "01_legalidad_huelgas_anual.png", "Legalidad por año: huelgas"),
        (
            "trabajadores_comprendidos",
            "02_legalidad_trabajadores_anual.png",
            "Legalidad por año: trabajadores comprendidos",
        ),
        (
            "horas_hombre_perdidas",
            "03_legalidad_horas_anual.png",
            "Legalidad por año: horas-hombre perdidas",
        ),
    ]:
        proc = f"{metric}_procedente"
        ilegal = f"{metric}_ilegal"
        fig, ax = plt.subplots(figsize=(13, 5))
        ax.bar(legalidad_resumen["anio"], legalidad_resumen[proc], label="procedente")
        ax.bar(
            legalidad_resumen["anio"],
            legalidad_resumen[ilegal],
            bottom=legalidad_resumen[proc],
            label="ilegal",
        )
        ax.set_title(title)
        ax.set_xlabel("Año")
        ax.set_ylabel(metric.replace("_", " "))
        ax.legend()
        fig.tight_layout()
        fig.savefig(GRAPH_DIR / filename, dpi=200, bbox_inches="tight")
        plt.close(fig)


def save_excel_bundle(
    master_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    annual_summary_df: pd.DataFrame,
    common_language_detail: pd.DataFrame,
    common_language_summary: pd.DataFrame,
    common_language_categories: pd.DataFrame,
    legalidad_long: pd.DataFrame,
    legalidad_resumen: pd.DataFrame,
    verif_long: pd.DataFrame,
    verif_resumen: pd.DataFrame,
    year_sector_long: pd.DataFrame,
    year_territory_long: pd.DataFrame,
) -> None:
    output_path = OUTPUT_DIR / "huelgas_maestra_1993_2024.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        master_df.to_excel(writer, sheet_name="datos", index=False)
        coverage_df.to_excel(writer, sheet_name="cobertura_modulos", index=False)
        annual_summary_df.to_excel(writer, sheet_name="resumen_anual", index=False)
        common_language_detail.to_excel(writer, sheet_name="idioma_comun", index=False)
        common_language_summary.to_excel(writer, sheet_name="idioma_modulos", index=False)
        common_language_categories.to_excel(writer, sheet_name="idioma_categorias", index=False)
        legalidad_long.to_excel(writer, sheet_name="legalidad_largo", index=False)
        legalidad_resumen.to_excel(writer, sheet_name="legalidad_resumen", index=False)
        verif_long.to_excel(writer, sheet_name="verif_calificacion", index=False)
        verif_resumen.to_excel(writer, sheet_name="verif_calif_resumen", index=False)
        year_sector_long.to_excel(writer, sheet_name="anio_sector", index=False)
        year_territory_long.to_excel(writer, sheet_name="anio_territorio", index=False)


def build_sector_territory_note() -> Path:
    note_path = OUTPUT_DIR / "nota_sector_territorio.md"
    text = """# Nota metodologica: sector y territorio

No se construyo un cruce directo `sector x territorio` dentro de la base maestra principal porque esa combinacion no se observa en los modulos simples anuales (`actividad` y `territorio`) sino en el cuadro cruzado `actividad x territorio` de la base complementaria.

La base maestra actual permite:

- `anio x sector`
- `anio x territorio` (usando solo nivel `regional` para evitar duplicacion)
- `legalidad x anio`

No permite observar directamente:

- `legalidad x sector`
- `legalidad x territorio`
- `sector x territorio` para toda la serie

Para esos cruces se requiere una extraccion adicional del cuadro cruzado `actividad x territorio`, que no forma parte del pipeline principal usado para homogenizar `1993-2024`.
"""
    note_path.write_text(text, encoding="utf-8")
    return note_path


def build_public_private_note() -> Path:
    note_path = OUTPUT_DIR / "nota_sector_publico_privado.md"
    text = """# Nota metodologica: sector privado y presencia del sector publico

Varios anuarios de huelgas del MTPE aluden en su titulo a `sector privado` o sugieren una cobertura privada. Sin embargo, en los cuadros de actividad economica aparecen de forma explicita categorias como:

- `administracion publica y defensa`
- `ensenanza`
- `servicios sociales y de salud`

## Que se hizo en la homologacion

- no se eliminaron esas filas
- no se recodificaron como si fueran `sector privado`
- no se imputo una separacion artificial entre conflicto publico y privado
- se conservaron tal como aparecen en la fuente y se homologaron a categorias observables del idioma comun, por ejemplo `administracion publica y defensa -> adm_publica`

## Interpretacion

El problema no es del pipeline sino de la propia fuente oficial: la titulacion historica de algunos anuarios no coincide plenamente con el contenido de los cuadros.

Por eso la base maestra debe leerse asi:

- `adm_publica`, `ensenanza` y `salud_social` son categorias validas observadas en la fuente
- su presencia documenta que el registro oficial incluye conflictividad fuera de un sector privado estricto
- esta inconsistencia conceptual debe reportarse en cualquier uso analitico o publicacion
"""
    note_path.write_text(text, encoding="utf-8")
    return note_path


def create_notebook() -> None:
    notebook_path = NOTEBOOK_DIR / "02_analisis_base_maestra.ipynb"
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Analisis de huelgas 1993-2024\n",
                    "\n",
                    "Este notebook lee la base maestra homologada, resume cobertura, grafica cruces posibles y verifica la consistencia del modulo de calificacion contra la fuente.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pathlib import Path\n",
                    "import pandas as pd\n",
                    "import matplotlib.pyplot as plt\n",
                    "\n",
                    "ROOT = Path.cwd().resolve()\n",
                    "if (ROOT / 'bases').exists() and (ROOT / 'notebooks').exists():\n",
                    "    project_root = ROOT\n",
                    "else:\n",
                    "    project_root = ROOT.parent\n",
                    "BASE = project_root / 'bases' / 'maestra'\n",
                    "GRAPH = BASE / 'graficos'\n",
                    "\n",
                    "master = pd.read_csv(BASE / 'huelgas_modulos_maestra_1993_2024.csv')\n",
                    "coverage = pd.read_csv(BASE / 'cobertura_modulos_1993_2024.csv')\n",
                    "legalidad = pd.read_csv(BASE / 'huelgas_legalidad_1996_2024_largo.csv')\n",
                    "legalidad_resumen = pd.read_csv(BASE / 'huelgas_legalidad_1996_2024_resumen_anual.csv')\n",
                    "verif = pd.read_csv(BASE / 'verificacion_calificacion_1993_2024_largo.csv')\n",
                    "verif_resumen = pd.read_csv(BASE / 'verificacion_calificacion_1993_2024_resumen.csv')\n",
                    "anio_sector = pd.read_csv(BASE / 'cruce_anio_sector_largo.csv')\n",
                    "anio_territorio = pd.read_csv(BASE / 'cruce_anio_territorio_regional_largo.csv')\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Cobertura y estructura\n",
                    "\n",
                    "La auditoria global y la cobertura por modulo ya vienen consolidadas en la carpeta `bases/maestra`.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "coverage.head(15)\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Legalidad por año\n",
                    "\n",
                    "Este es el cruce observable directamente con la fuente. No existe un cruce directo `legalidad x sector` ni `legalidad x territorio` en los anuarios usados para la base principal.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "legalidad_resumen.head()\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "for metric, title in [\n",
                    "    ('huelgas', 'Legalidad por año: huelgas'),\n",
                    "    ('trabajadores_comprendidos', 'Legalidad por año: trabajadores comprendidos'),\n",
                    "    ('horas_hombre_perdidas', 'Legalidad por año: horas-hombre perdidas'),\n",
                    "]:\n",
                    "    proc = f'{metric}_procedente'\n",
                    "    ilegal = f'{metric}_ilegal'\n",
                    "    fig, ax = plt.subplots(figsize=(13, 4))\n",
                    "    ax.bar(legalidad_resumen['anio'], legalidad_resumen[proc], label='procedente')\n",
                    "    ax.bar(legalidad_resumen['anio'], legalidad_resumen[ilegal], bottom=legalidad_resumen[proc], label='ilegal')\n",
                    "    ax.set_title(title)\n",
                    "    ax.legend()\n",
                    "    plt.show()\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Cruce año x sector\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "pivot_sector = pd.read_csv(BASE / 'cruce_anio_sector_huelgas_pivot.csv').set_index('anio')\n",
                    "pivot_sector.head()\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "heat = pivot_sector.copy()\n",
                    "top_cols = heat.sum(axis=0).sort_values(ascending=False).head(12).index\n",
                    "heat = heat[top_cols]\n",
                    "fig, ax = plt.subplots(figsize=(12, 8))\n",
                    "im = ax.imshow(heat.values, aspect='auto', cmap='YlOrRd')\n",
                    "ax.set_xticks(range(len(heat.columns)))\n",
                    "ax.set_xticklabels(heat.columns, rotation=90)\n",
                    "ax.set_yticks(range(len(heat.index)))\n",
                    "ax.set_yticklabels(heat.index.astype(str))\n",
                    "ax.set_title('Año x sector (huelgas, top 12 sectores)')\n",
                    "fig.colorbar(im, ax=ax, label='Huelgas')\n",
                    "plt.show()\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Cruce año x territorio\n",
                    "\n",
                    "Se usa solo `nivel_territorial = regional` para evitar duplicar con zonas.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "pivot_territorio = pd.read_csv(BASE / 'cruce_anio_territorio_regional_huelgas_pivot.csv').set_index('anio')\n",
                    "pivot_territorio.head()\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "heat = pivot_territorio.copy()\n",
                    "top_cols = heat.sum(axis=0).sort_values(ascending=False).head(12).index\n",
                    "heat = heat[top_cols]\n",
                    "fig, ax = plt.subplots(figsize=(12, 8))\n",
                    "im = ax.imshow(heat.values, aspect='auto', cmap='YlGnBu')\n",
                    "ax.set_xticks(range(len(heat.columns)))\n",
                    "ax.set_xticklabels(heat.columns, rotation=90)\n",
                    "ax.set_yticks(range(len(heat.index)))\n",
                    "ax.set_yticklabels(heat.index.astype(str))\n",
                    "ax.set_title('Año x territorio regional (huelgas, top 12 territorios)')\n",
                    "fig.colorbar(im, ax=ax, label='Huelgas')\n",
                    "plt.show()\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Sector x territorio\n",
                    "\n",
                    "Ese cruce **no forma parte de la base maestra principal** porque requiere el cuadro cruzado `actividad x territorio` de la base complementaria. La nota metodologica consolidada esta en `bases/maestra/nota_sector_territorio.md`.\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Verificación del módulo de calificación\n",
                    "\n",
                    "Aquí se comprueba, para cada año con módulo disponible, que `procedente + ilegal` coincide con el `TOTAL` de la hoja fuente en las tres métricas.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "verif_resumen\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    master_df, coverage_df, validation_df, annual_summary_df = collect_outputs()
    common_language_detail, common_language_summary, common_language_categories = build_common_language_reference(master_df)
    legalidad_long, legalidad_resumen = build_legalidad(master_df)
    verif_long, verif_resumen = build_calificacion_verification(validation_df)
    year_sector_long, year_sector_pivot = build_year_sector(master_df)
    year_territory_long, year_territory_pivot = build_year_territory(master_df)

    master_df.to_csv(OUTPUT_DIR / "huelgas_modulos_maestra_1993_2024.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(OUTPUT_DIR / "cobertura_modulos_1993_2024.csv", index=False, encoding="utf-8-sig")
    annual_summary_df.to_csv(OUTPUT_DIR / "resumen_anual_1993_2024.csv", index=False, encoding="utf-8-sig")
    common_language_detail.to_csv(OUTPUT_DIR / "diccionario_idioma_comun_1993_2024.csv", index=False, encoding="utf-8-sig")
    common_language_summary.to_csv(OUTPUT_DIR / "resumen_idioma_comun_modulos.csv", index=False, encoding="utf-8-sig")
    common_language_categories.to_csv(OUTPUT_DIR / "tabla_lenguaje_comun_categorias.csv", index=False, encoding="utf-8-sig")
    legalidad_long.to_csv(OUTPUT_DIR / "huelgas_legalidad_1996_2024_largo.csv", index=False, encoding="utf-8-sig")
    legalidad_resumen.to_csv(OUTPUT_DIR / "huelgas_legalidad_1996_2024_resumen_anual.csv", index=False, encoding="utf-8-sig")
    verif_long.to_csv(OUTPUT_DIR / "verificacion_calificacion_1993_2024_largo.csv", index=False, encoding="utf-8-sig")
    verif_resumen.to_csv(OUTPUT_DIR / "verificacion_calificacion_1993_2024_resumen.csv", index=False, encoding="utf-8-sig")
    year_sector_long.to_csv(OUTPUT_DIR / "cruce_anio_sector_largo.csv", index=False, encoding="utf-8-sig")
    year_sector_pivot.to_csv(OUTPUT_DIR / "cruce_anio_sector_huelgas_pivot.csv", index=False, encoding="utf-8-sig")
    year_territory_long.to_csv(OUTPUT_DIR / "cruce_anio_territorio_regional_largo.csv", index=False, encoding="utf-8-sig")
    year_territory_pivot.to_csv(OUTPUT_DIR / "cruce_anio_territorio_regional_huelgas_pivot.csv", index=False, encoding="utf-8-sig")

    save_excel_bundle(
        master_df,
        coverage_df,
        annual_summary_df,
        common_language_detail,
        common_language_summary,
        common_language_categories,
        legalidad_long,
        legalidad_resumen,
        verif_long,
        verif_resumen,
        year_sector_long,
        year_territory_long,
    )
    save_legalidad_plots(legalidad_resumen)
    save_heatmap(
        year_sector_pivot,
        "Año x sector (huelgas, top 12 sectores)",
        GRAPH_DIR / "04_anio_sector_huelgas.png",
        top_n=12,
    )
    save_heatmap(
        year_territory_pivot,
        "Año x territorio regional (huelgas, top 12 territorios)",
        GRAPH_DIR / "05_anio_territorio_regional_huelgas.png",
        top_n=12,
    )
    build_sector_territory_note()
    build_public_private_note()
    create_notebook()

    print(f"[ok] base maestra -> {OUTPUT_DIR / 'huelgas_modulos_maestra_1993_2024.csv'}")
    print(f"[ok] idioma comun -> {OUTPUT_DIR / 'diccionario_idioma_comun_1993_2024.csv'}")
    print(f"[ok] legalidad -> {OUTPUT_DIR / 'huelgas_legalidad_1996_2024_largo.csv'}")
    print(f"[ok] verificacion calificacion -> {OUTPUT_DIR / 'verificacion_calificacion_1993_2024_resumen.csv'}")
    print(f"[ok] notebook -> {NOTEBOOK_DIR / '02_analisis_base_maestra.ipynb'}")


if __name__ == "__main__":
    main()
