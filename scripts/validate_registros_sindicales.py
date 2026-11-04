"""Valida estructura, duplicados, sumas y celdas fuente de Registro Sindical."""
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "registros_sindicales"


def main():
    private = pd.read_csv(OUT / "registros_privados_anual.csv")
    public = pd.read_csv(OUT / "registros_publicos_anual.csv")
    activity = pd.read_csv(OUT / "sindicatos_privados_actividad_anual.csv")
    stock = pd.read_csv(OUT / "organizaciones_vigentes_2002.csv")
    controls = pd.read_csv(OUT / "controles.csv")

    assert private["anio"].tolist() == list(range(1993, 2026))
    assert public["anio"].tolist() == list(range(2004, 2026))
    assert activity.groupby("anio")["sector_analitico"].apply(lambda s: (s == "total_nacional").sum()).eq(1).all()
    assert not private["anio"].duplicated().any()
    assert not public["anio"].duplicated().any()
    assert not activity.duplicated(["anio", "actividad"]).any()
    assert (activity["diferencia_total"] == 0).all()
    flagged = controls[controls["resultado"] != "ok"]
    # El cuadro por actividad publicado en 2008 suma 203 sindicatos; la serie
    # retrospectiva del Anuario 2025 revisa ese año a 201. Se conserva la ruptura.
    assert len(flagged) == 1, flagged.to_dict("records")
    assert flagged.iloc[0]["control"] == "total_actividad_igual_registros_sindicatos_privados"
    assert flagged.iloc[0]["anio"] == 2008 and flagged.iloc[0]["diferencia"] == 2
    assert stock.loc[0, "organizaciones_vigentes_sindicatos"] == 2703
    assert private.loc[private["anio"] == 2025, "registros_sindicatos"].iat[0] == 173
    assert public.loc[public["anio"] == 2025, "registros_sindicatos"].iat[0] == 277
    print("OK: series, duplicados, sumas mensuales y stock verificados; revisión 2008 documentada.")


if __name__ == "__main__":
    main()
