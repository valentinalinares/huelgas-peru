"""Convenios colectivos de carácter supraregional o nacional (D.S. 017-2012-TR,
art. 3, inc. d), 2013-2019.

Los anuarios 2017-2019 del MTPE indican en el cuadro nacional de convenios por
actividad (C-28) que no incluye estos convenios, y los publican aparte en el
cuadro C-40. La serie retrospectiva del Anuario 2025 (C-56) conserva para
2013-2019 los mismos valores sin ellos. Desde el Anuario 2020 el cuadro aparte
ya no aparece y la nota de exclusión tampoco.

Fuente principal: C-40 del Anuario 2019 (2013-2019). Controles: C-40 de los
anuarios 2017 y 2018, suma de actividades y comparación con C-56.

Uso, desde la raíz del proyecto:
    python scripts/extract_convenios_supraregionales.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import unicodedata
import warnings
from pathlib import Path

import openpyxl

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

ROOT = Path(__file__).resolve().parents[1]
FUENTES = {  # anuario: (archivo, hoja)
    2019: ("anuarios/2019/CAPITULO 02 - NEGOCIACIONES COLECTIVAS.xlsx", "C-40"),
    2018: ("anuarios/2018/CAPITULO 02 - NEGOCIACIONES COLECTIVAS (1).xlsx", "C-40"),
    2017: ("anuarios/2017/CAPITULO 02 - NEGOCIACIONES COLECTIVAS.xlsx", "nuevo 5"),
}
C56 = ROOT / "bases/negociacion_colectiva/base_negociacion_colectiva_c56_1995_2025.csv"
SALIDA = ROOT / "bases/negociacion_colectiva/complementos"
NOTA = ("Convenios registrados en el marco del D.S. 017-2012-TR, art. 3, inc. d. "
        "Los anuarios 2017-2019 indican que no están incluidos en el cuadro nacional por actividad.")


def norm(texto: object) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(t.upper().split())


def sector_de(rotulo: str) -> str:
    t = norm(rotulo)
    if "MINAS" in t:
        return "mineria"
    if "MANUFACT" in t:
        return "manufactura"
    if t == "TOTAL":
        return "total_nacional"
    return "otra_actividad"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leer_c40(anuario: int) -> list[dict]:
    archivo, hoja = FUENTES[anuario]
    path = ROOT / archivo
    ws = openpyxl.load_workbook(path, data_only=True)[hoja]
    filas = list(ws.iter_rows())
    huella = sha256(path)
    colmap, obs = {}, []
    for fila in filas:
        anios = {c.column: int(c.value) for c in fila
                 if isinstance(c.value, (int, float)) and 2012 < c.value < 2030}
        if not colmap and len(anios) >= 4 and not any(isinstance(c.value, str) and c.value.strip() for c in fila):
            colmap = anios
            continue
        if not colmap:
            continue
        textos = [c for c in fila if isinstance(c.value, str) and c.value.strip() and c.column < min(colmap)]
        if not textos:
            continue
        if norm(textos[0].value).startswith("FUENTE"):
            break
        rotulo = " ".join(str(textos[-1].value).split())
        por_col = {c.column: c for c in fila}
        for col, anio in colmap.items():
            c = por_col.get(col)
            valor = c.value if c is not None else None
            obs.append({"anio": anio, "actividad": rotulo, "sector_analitico": sector_de(rotulo),
                        "convenios": valor if isinstance(valor, (int, float)) else None,
                        "valor_original": "" if valor is None else str(valor),
                        "anuario": anuario, "fuente_archivo": archivo, "fuente_hoja": hoja,
                        "fuente_celda": c.coordinate if c is not None else "", "sha256": huella})
    if not obs:
        raise SystemExit(f"No se pudo leer el cuadro supraregional del anuario {anuario}")
    return obs


def escribir(path: Path, filas: list[dict], campos: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


def main() -> int:
    ediciones = {a: leer_c40(a) for a in FUENTES}
    base = ediciones[2019]
    for r in base:
        r["nota"] = NOTA
    controles = []

    def control(tipo, anio, sector, observado, referencia, referencia_txt):
        ok = observado is not None and referencia is not None and abs(observado - referencia) < 0.5
        controles.append({"control": tipo, "anio": anio, "sector": sector, "valor": observado,
                          "referencia": referencia, "fuente_referencia": referencia_txt,
                          "resultado": "coincide" if ok else "difiere"})

    # Suma de actividades = total publicado
    for anio in sorted({r["anio"] for r in base}):
        filas = [r for r in base if r["anio"] == anio]
        total = next(r["convenios"] for r in filas if r["sector_analitico"] == "total_nacional")
        suma = sum(r["convenios"] or 0 for r in filas if r["sector_analitico"] != "total_nacional")
        control("suma_actividades_vs_total", anio, "total_nacional", suma, total, "C-40 Anuario 2019")
    # Ediciones 2017 y 2018 contra 2019
    clave = lambda r: (r["anio"], norm(r["actividad"]))
    v19 = {clave(r): r["convenios"] for r in base}
    for anuario in (2017, 2018):
        for r in ediciones[anuario]:
            control(f"anuario_{anuario}_vs_2019", r["anio"], r["sector_analitico"] if r["sector_analitico"] != "otra_actividad"
                    else norm(r["actividad"]).lower()[:40], r["convenios"], v19.get(clave(r)), f"C-40 Anuario {anuario}")

    # Serie referencial: C-56 (sin supraregionales) + C-40
    c56 = {}
    with C56.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            sector = {"minas_canteras": "mineria", "manufactura": "manufactura",
                      "total_nacional": "total_nacional"}.get(r["sector_id"])
            if sector and 2013 <= int(r["anio"]) <= 2019:
                c56[(int(r["anio"]), sector)] = int(r["convenios_colectivos"])
    referencial = []
    for r in base:
        if r["sector_analitico"] == "otra_actividad":
            continue
        k = (r["anio"], r["sector_analitico"])
        referencial.append({"anio": r["anio"], "sector": r["sector_analitico"],
                            "convenios_c56_sin_supraregionales": c56.get(k),
                            "convenios_supraregionales_c40": r["convenios"],
                            "suma_referencial": (c56.get(k) or 0) + (r["convenios"] or 0),
                            "nota": "Suma referencial: supone que ambos cuadros no se superponen, como indica la nota 2/ de los anuarios 2017-2019."})
    referencial.sort(key=lambda r: (r["anio"], ["mineria", "manufactura", "total_nacional"].index(r["sector"])))

    escribir(SALIDA / "convenios_supraregionales_2013_2019.csv", base,
             ["anio", "actividad", "sector_analitico", "convenios", "valor_original", "anuario",
              "fuente_archivo", "fuente_hoja", "fuente_celda", "sha256", "nota"])
    escribir(SALIDA / "convenios_con_supraregionales_2013_2019.csv", referencial,
             ["anio", "sector", "convenios_c56_sin_supraregionales", "convenios_supraregionales_c40",
              "suma_referencial", "nota"])
    escribir(SALIDA / "controles_supraregionales.csv", controles,
             ["control", "anio", "sector", "valor", "referencia", "fuente_referencia", "resultado"])
    conteo = {}
    for c in controles:
        conteo[c["resultado"]] = conteo.get(c["resultado"], 0) + 1
    print(json.dumps({"observaciones": len(base), "controles": conteo}, ensure_ascii=False))
    for r in referencial:
        if r["sector"] == "mineria":
            print(r["anio"], "minería:", r["convenios_c56_sin_supraregionales"], "+", r["convenios_supraregionales_c40"],
                  "=", r["suma_referencial"])
    if conteo.get("difiere"):
        print("ERROR: hay controles que difieren; revisar controles_supraregionales.csv", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
