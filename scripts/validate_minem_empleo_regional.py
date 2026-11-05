"""Valida el módulo externo de empleo minero regional MINEM."""
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "minem_empleo_regional"


def main():
    monthly = pd.read_csv(OUT / "empleo_minero_departamental_mensual_2020_2026.csv")
    annual = pd.read_csv(OUT / "empleo_minero_departamental_promedio_2020_2026.csv")
    controls = pd.read_csv(OUT / "controles.csv")
    assert len(monthly) == 2080 and len(annual) == 182 and len(controls) == 182
    assert not monthly.duplicated(["anio", "mes", "departamento_id"]).any()
    assert not annual.duplicated(["anio", "departamento_id"]).any()
    assert (controls["resultado"] == "ok").all(), controls[controls["resultado"] != "ok"].to_dict("records")
    expected = {2020: 178148.3333333333, 2021: 217320.6666666667, 2022: 232189.5833333333, 2023: 226236.8333333333, 2024: 239653.5833333333, 2025: 266311.1666666667, 2026: 286366.875}
    total = annual[annual["departamento_id"] == "total_nacional"].set_index("anio")["empleo_promedio_publicado"]
    for year, value in expected.items():
        assert abs(total.loc[year] - value) < 1e-6, (year, total.loc[year], value)
    print("OK: claves, 182 promedios y totales nacionales 2020–2026 verificados.")


if __name__ == "__main__":
    main()
