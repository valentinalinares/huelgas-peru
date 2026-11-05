"""Extrae empleo minero departamental de la estadística oficial MINEM."""
from pathlib import Path
import hashlib
import re
import unicodedata

import pandas as pd
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fuentes_externas" / "minem_empleo" / "empleo_minero_2020_agosto_2026.xlsx"
OUT = ROOT / "bases" / "minem_empleo_regional"
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]


def norm(value):
    text = "".join(c for c in unicodedata.normalize("NFD", str(value).upper()) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = pd.read_excel(SOURCE, sheet_name="Empleo Minero", header=None)
    assert "EMPLEO MINERO A NIVEL DEPARTAMENTAL" in norm(data.iat[1, 0])
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    monthly, annual, controls = [], [], []
    for r in range(5, 31):
        original = str(data.iat[r, 0]).strip()
        department = "total_nacional" if norm(original) == "TOTAL GENERAL" else norm(original).lower().replace(" ", "_")
        for year in range(2020, 2027):
            start = 1 + 13 * (year - 2020)
            values = []
            months_available = 12 if year <= 2025 else 8
            for month_number in range(1, months_available + 1):
                value = pd.to_numeric(data.iat[r, start + month_number - 1], errors="coerce")
                assert pd.notna(value), (r, year, month_number)
                values.append(value)
                monthly.append({
                    "anio": year,
                    "mes": month_number,
                    "mes_nombre": MONTHS[month_number - 1],
                    "departamento_id": department,
                    "departamento_original": original,
                    "empleo_minero": value,
                    "unidad": "trabajadores",
                    "cobertura": "empleo_directo_mineria_estamin",
                    "estado_dato": "preliminar",
                    "fuente_archivo": str(SOURCE.relative_to(ROOT)),
                    "fuente_hoja": "Empleo Minero",
                    "fuente_celda": f"{get_column_letter(start+month_number)}{r+1}",
                    "sha256": sha,
                })
            published = pd.to_numeric(data.iat[r, start + 12], errors="coerce")
            calculated = sum(values) / len(values)
            diff = calculated - published
            annual.append({
                "anio": year,
                "meses_disponibles": months_available,
                "periodo": "enero-diciembre" if months_available == 12 else "enero-agosto",
                "departamento_id": department,
                "departamento_original": original,
                "empleo_promedio_publicado": published,
                "empleo_promedio_calculado": calculated,
                "unidad": "trabajadores",
                "estado_dato": "preliminar",
                "fuente_archivo": str(SOURCE.relative_to(ROOT)),
                "fuente_hoja": "Empleo Minero",
                "fuente_celda": f"{get_column_letter(start+13)}{r+1}",
                "sha256": sha,
            })
            controls.append({
                "control": "promedio_meses_igual_promedio_publicado",
                "anio": year,
                "departamento_id": department,
                "meses": months_available,
                "valor_publicado": published,
                "valor_calculado": calculated,
                "diferencia": diff,
                "resultado": "ok" if abs(diff) < 1e-8 else "revisar",
            })
    monthly = pd.DataFrame(monthly)
    annual = pd.DataFrame(annual)
    controls = pd.DataFrame(controls)
    monthly.to_csv(OUT / "empleo_minero_departamental_mensual_2020_2026.csv", index=False, encoding="utf-8-sig")
    annual.to_csv(OUT / "empleo_minero_departamental_promedio_2020_2026.csv", index=False, encoding="utf-8-sig")
    controls.to_csv(OUT / "controles.csv", index=False, encoding="utf-8-sig")
    print(f"OK: {len(monthly)} filas mensuales, {len(annual)} promedios y {len(controls)} controles.")


if __name__ == "__main__":
    main()
