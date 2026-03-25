from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "shapes"
TERRITORY_TOLERANCE = 0.005
PROVINCE_TOLERANCE = 0.003
SOURCE_CANDIDATES = [
    PROJECT_ROOT / "data" / "districts" / "DISTRITOS.shp",
    PROJECT_ROOT / "data" / "shape_file" / "DISTRITOS.shp",
]


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def resolve_source() -> Path:
    for candidate in SOURCE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No se encontro un shapefile distrital fuente en data/districts ni data/shape_file.")


def build_provinces(districts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    provincias = (
        districts[["IDDPTO", "DEPARTAMEN", "IDPROV", "PROVINCIA", "geometry"]]
        .dissolve(by=["IDDPTO", "DEPARTAMEN", "IDPROV", "PROVINCIA"], as_index=False)
        .reset_index(drop=True)
    )
    provincias["departamento_homologado"] = provincias["DEPARTAMEN"].map(normalize_text)
    provincias["provincia_homologada"] = provincias["PROVINCIA"].map(normalize_text)
    provincias = provincias.rename(
        columns={
            "IDDPTO": "iddpto",
            "DEPARTAMEN": "departamento_original",
            "IDPROV": "idprov",
            "PROVINCIA": "provincia_original",
        }
    )
    return provincias[
        [
            "iddpto",
            "departamento_original",
            "departamento_homologado",
            "idprov",
            "provincia_original",
            "provincia_homologada",
            "geometry",
        ]
    ]


def map_huelga_territory(row: pd.Series) -> str:
    dept = str(row["DEPARTAMEN"]).strip().upper()
    prov = str(row["PROVINCIA"]).strip().upper()
    if dept == "LIMA" and prov == "LIMA":
        return "lima_metropolitana"
    if dept == "LIMA":
        return "lima_provincia"
    return normalize_text(dept)


def build_huelga_territories(districts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    territories = districts[["DEPARTAMEN", "PROVINCIA", "geometry"]].copy()
    territories["territorio_homologado"] = territories.apply(map_huelga_territory, axis=1)
    dissolved = territories.dissolve(by="territorio_homologado", as_index=False).reset_index(drop=True)
    labels = {
        "lima_metropolitana": "Lima Metropolitana",
        "lima_provincia": "Lima Provincia",
    }
    dissolved["territorio_label"] = dissolved["territorio_homologado"].map(
        lambda x: labels.get(x, str(x).replace("_", " ").title())
    )
    dissolved["nivel_mapa"] = "territorio_homologado"
    return dissolved[["territorio_homologado", "territorio_label", "nivel_mapa", "geometry"]]


def build_crosswalk(territories: gpd.GeoDataFrame) -> pd.DataFrame:
    notes = {
        "lima_metropolitana": "Se construye con la provincia de Lima.",
        "lima_provincia": "Se construye con el resto de provincias del departamento de Lima.",
        "callao": "Equivale al Callao como unidad propia.",
        "lima": "Categoria historica de la fuente; para mapas temporales se agrega a lima_total.",
    }
    rows = []
    for territorio in territories["territorio_homologado"].tolist():
        territorio_mapa = "lima_total" if territorio in {"lima_metropolitana", "lima_provincia"} else territorio
        rows.append(
            {
                "territorio_fuente": territorio,
                "territorio_label_fuente": str(territorio).replace("_", " ").title(),
                "territorio_mapa": territorio_mapa,
                "territorio_label_mapa": "Lima Total" if territorio_mapa == "lima_total" else str(territorio_mapa).replace("_", " ").title(),
                "nivel_mapa": "territorio_homologado",
                "nota": notes.get(territorio, "Derivado del departamento original."),
            }
        )
    rows.append(
        {
            "territorio_fuente": "lima",
            "territorio_label_fuente": "Lima",
            "territorio_mapa": "lima_total",
            "territorio_label_mapa": "Lima Total",
            "nivel_mapa": "territorio_historico",
            "nota": notes["lima"],
        }
    )
    crosswalk = pd.DataFrame(rows)
    return crosswalk.sort_values(["territorio_mapa", "territorio_fuente"]).reset_index(drop=True)


def build_huelga_territories_lima_total(territories: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    collapsed = territories.copy()
    collapsed["territorio_mapa"] = collapsed["territorio_homologado"].replace(
        {"lima_metropolitana": "lima_total", "lima_provincia": "lima_total"}
    )
    dissolved = collapsed.dissolve(by="territorio_mapa", as_index=False).reset_index(drop=True)
    dissolved["territorio_label"] = dissolved["territorio_mapa"].map(
        lambda x: "Lima Total" if x == "lima_total" else str(x).replace("_", " ").title()
    )
    dissolved["nivel_mapa"] = "territorio_mapa"
    return dissolved[["territorio_mapa", "territorio_label", "nivel_mapa", "geometry"]]


def simplify_frame(frame: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    simplified = frame.copy()
    simplified["geometry"] = simplified.geometry.simplify(tolerance, preserve_topology=True)
    return simplified


def main() -> None:
    source_path = resolve_source()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    districts = gpd.read_file(source_path).to_crs(epsg=4326)
    provinces = build_provinces(districts)
    territories = build_huelga_territories(districts)
    territories_lima_total = build_huelga_territories_lima_total(territories)
    provinces = simplify_frame(provinces, PROVINCE_TOLERANCE)
    territories = simplify_frame(territories, TERRITORY_TOLERANCE)
    territories_lima_total = simplify_frame(territories_lima_total, TERRITORY_TOLERANCE)
    crosswalk = build_crosswalk(territories)

    territories.to_file(OUTPUT_DIR / "peru_territorios_huelga.geojson", driver="GeoJSON")
    territories_lima_total.to_file(OUTPUT_DIR / "peru_territorios_huelga_lima_total.geojson", driver="GeoJSON")
    provinces.to_file(OUTPUT_DIR / "peru_provincias.geojson", driver="GeoJSON")
    crosswalk.to_csv(OUTPUT_DIR / "equivalencias_territorio_mapa.csv", index=False)

    print(f"[ok] territorios -> {OUTPUT_DIR / 'peru_territorios_huelga.geojson'}")
    print(f"[ok] territorios lima total -> {OUTPUT_DIR / 'peru_territorios_huelga_lima_total.geojson'}")
    print(f"[ok] provincias -> {OUTPUT_DIR / 'peru_provincias.geojson'}")
    print(f"[ok] equivalencias -> {OUTPUT_DIR / 'equivalencias_territorio_mapa.csv'}")


if __name__ == "__main__":
    main()
