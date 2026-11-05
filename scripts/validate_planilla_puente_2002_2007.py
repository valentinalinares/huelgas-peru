"""Valida el puente histórico de Hojas de Resumen de Planillas."""
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "planilla_electronica"


def main():
    base = pd.read_csv(OUT / "puente_junio_2002_2007.csv")
    summary = pd.read_csv(OUT / "resumen_puente_junio_2002_2007.csv")
    controls = pd.read_csv(OUT / "controles_puente_junio_2002_2007.csv")
    assert len(base) == 54 and len(summary) == 18 and len(controls) == 54
    assert not base.duplicated(["anio", "sector_id", "indicador"]).any()
    assert set(base["anio"]) == set(range(2002, 2008))
    assert set(base["sector_id"]) == {"mineria", "manufactura", "total_nacional"}
    assert set(base["indicador"]) == {"empleo", "ingreso", "negociacion"}
    assert not (controls["resultado"] == "revisar").any(), controls[controls["resultado"] == "revisar"].to_dict("records")
    assert (controls["resultado"] == "ok_con_salvedad_metodologica_2007").sum() == 3
    assert (controls["resultado"] == "ok_redondeo").sum() == 1
    assert summary["tasa_sujetos_negociacion"].between(0, 1).all()
    print("OK: 50 controles exactos, 1 redondeo, 3 salvedades de ingreso 2007 y 18 tasas verificadas.")


if __name__ == "__main__":
    main()
