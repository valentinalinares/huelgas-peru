from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAESTRA_DIR = ROOT / "bases" / "maestra"
CRUCE_DIR = ROOT / "bases" / "cruce_sector_territorio"
OUTPUT_DIR = ROOT / "bases" / "reportes"


def build_resumen_ejecutivo_anual() -> pd.DataFrame:
    anio_sector = pd.read_csv(MAESTRA_DIR / "cruce_anio_sector_largo.csv")
    anio_territorio = pd.read_csv(MAESTRA_DIR / "cruce_anio_territorio_regional_largo.csv")
    legalidad = pd.read_csv(MAESTRA_DIR / "huelgas_legalidad_1996_2024_resumen_anual.csv")

    totals = (
        anio_sector.groupby("anio", as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .rename(
            columns={
                "huelgas": "huelgas_total",
                "trabajadores_comprendidos": "trabajadores_total",
                "horas_hombre_perdidas": "horas_total",
            }
        )
    )

    sector_top = (
        anio_sector.sort_values(["anio", "huelgas", "trabajadores_comprendidos"], ascending=[True, False, False])
        .drop_duplicates("anio")
        .rename(
            columns={
                "categoria_homologada_agregada": "sector_principal_huelgas",
                "huelgas": "sector_principal_huelgas_valor",
                "trabajadores_comprendidos": "sector_principal_trabajadores",
                "horas_hombre_perdidas": "sector_principal_horas",
            }
        )[
            [
                "anio",
                "sector_principal_huelgas",
                "sector_principal_huelgas_valor",
                "sector_principal_trabajadores",
                "sector_principal_horas",
            ]
        ]
    )

    territorio_top = (
        anio_territorio.sort_values(["anio", "huelgas", "trabajadores_comprendidos"], ascending=[True, False, False])
        .drop_duplicates("anio")
        .rename(
            columns={
                "categoria_homologada_agregada": "territorio_principal_huelgas",
                "huelgas": "territorio_principal_huelgas_valor",
                "trabajadores_comprendidos": "territorio_principal_trabajadores",
                "horas_hombre_perdidas": "territorio_principal_horas",
            }
        )[
            [
                "anio",
                "territorio_principal_huelgas",
                "territorio_principal_huelgas_valor",
                "territorio_principal_trabajadores",
                "territorio_principal_horas",
            ]
        ]
    )

    legalidad = legalidad.copy()
    legalidad["pct_ilegal_huelgas"] = (
        legalidad["huelgas_ilegal"] / legalidad["huelgas_total_observado"]
    )
    legalidad = legalidad[
        [
            "anio",
            "huelgas_ilegal",
            "huelgas_procedente",
            "huelgas_total_observado",
            "pct_ilegal_huelgas",
        ]
    ]

    resumen = totals.merge(sector_top, on="anio", how="left").merge(territorio_top, on="anio", how="left")
    resumen = resumen.merge(legalidad, on="anio", how="left")
    resumen["pct_sector_principal_huelgas"] = (
        resumen["sector_principal_huelgas_valor"] / resumen["huelgas_total"]
    )
    resumen["pct_territorio_principal_huelgas"] = (
        resumen["territorio_principal_huelgas_valor"] / resumen["huelgas_total"]
    )
    return resumen.sort_values("anio")


def build_resumen_region_anual() -> pd.DataFrame:
    anio_territorio = pd.read_csv(MAESTRA_DIR / "cruce_anio_territorio_regional_largo.csv")

    annual_totals = (
        anio_territorio.groupby("anio", as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .rename(
            columns={
                "huelgas": "huelgas_anio_total",
                "trabajadores_comprendidos": "trabajadores_anio_total",
                "horas_hombre_perdidas": "horas_anio_total",
            }
        )
    )

    region = anio_territorio.rename(columns={"categoria_homologada_agregada": "region"})
    region = region.merge(annual_totals, on="anio", how="left")
    region["participacion_huelgas_anual"] = region["huelgas"] / region["huelgas_anio_total"]
    region["participacion_trabajadores_anual"] = (
        region["trabajadores_comprendidos"] / region["trabajadores_anio_total"]
    )
    region["participacion_horas_anual"] = (
        region["horas_hombre_perdidas"] / region["horas_anio_total"]
    )
    region["rank_region_huelgas"] = (
        region.groupby("anio")["huelgas"].rank(method="first", ascending=False).astype(int)
    )
    return region.sort_values(["anio", "rank_region_huelgas", "region"])


def build_resumen_region_sector_dominante() -> pd.DataFrame:
    cross = pd.read_csv(CRUCE_DIR / "sector_territorio_2001_2024.csv")
    regional = cross[cross["nivel_territorial"] == "regional"].copy()

    grouped = (
        regional.groupby(
            ["anio", "territorio_homologado_agregado", "actividad_homologada_agregada"],
            as_index=False,
        )[["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]]
        .sum()
    )

    totals = (
        grouped.groupby(["anio", "territorio_homologado_agregado"], as_index=False)[
            ["huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas"]
        ]
        .sum()
        .rename(
            columns={
                "huelgas": "huelgas_region_total",
                "trabajadores_comprendidos": "trabajadores_region_total",
                "horas_hombre_perdidas": "horas_region_total",
            }
        )
    )

    top = (
        grouped.sort_values(
            ["anio", "territorio_homologado_agregado", "huelgas", "trabajadores_comprendidos"],
            ascending=[True, True, False, False],
        )
        .drop_duplicates(["anio", "territorio_homologado_agregado"])
        .merge(totals, on=["anio", "territorio_homologado_agregado"], how="left")
        .rename(
            columns={
                "territorio_homologado_agregado": "region",
                "actividad_homologada_agregada": "sector_principal_region",
                "huelgas": "sector_principal_huelgas",
                "trabajadores_comprendidos": "sector_principal_trabajadores",
                "horas_hombre_perdidas": "sector_principal_horas",
            }
        )
    )
    top["participacion_sector_principal_huelgas"] = (
        top["sector_principal_huelgas"] / top["huelgas_region_total"]
    )
    return top.sort_values(["anio", "region"])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resumen_anual = build_resumen_ejecutivo_anual()
    resumen_region = build_resumen_region_anual()
    resumen_region_sector = build_resumen_region_sector_dominante()

    resumen_anual.to_csv(OUTPUT_DIR / "resumen_ejecutivo_anual.csv", index=False, encoding="utf-8-sig")
    resumen_region.to_csv(OUTPUT_DIR / "resumen_region_anual.csv", index=False, encoding="utf-8-sig")
    resumen_region_sector.to_csv(
        OUTPUT_DIR / "resumen_region_sector_dominante_2001_2024.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"[ok] {OUTPUT_DIR / 'resumen_ejecutivo_anual.csv'}")
    print(f"[ok] {OUTPUT_DIR / 'resumen_region_anual.csv'}")
    print(f"[ok] {OUTPUT_DIR / 'resumen_region_sector_dominante_2001_2024.csv'}")


if __name__ == "__main__":
    main()
