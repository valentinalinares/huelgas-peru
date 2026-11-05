"""Serie de huelgas para minería, manufactura y total nacional, 1970-2025.

Fuentes: Anuario Estadístico Sectorial 2025 del MTPE, capítulo 4.
- C-92: total nacional de huelgas, trabajadores comprendidos y horas-hombre
  perdidas, 1970-2025.
- C-93: las mismas variables por actividad económica, 1990-2025.
- C-94: actividad económica en 2025, usado solo como control.

La base maestra del artículo (bases/maestra y bases/reportes) se usa como
control para 1994-2025 y no se modifica.

Uso, desde la raíz del proyecto:
    python scripts/build_huelgas_sectores.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import unicodedata
import warnings
from pathlib import Path

import openpyxl

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

FUENTE = Path("anuarios/2025/CAP 04 - HUELGAS_2025_v2-JTR_OK_19_05_2026_FINAL.xlsx")
SALIDA = Path("bases/huelgas_sectores")
INDICADORES = ("huelgas", "trabajadores_comprendidos", "horas_hombre_perdidas")
SECTORES = ("mineria", "manufactura", "total_nacional")
NOTA_MINERIA = ("Explotación de minas y canteras según el MTPE: incluye petróleo y gas natural "
                "y no equivale a minería metálica; puede excluir contratistas clasificados en otras actividades.")
NOTA_HHP = "Puede incluir horas de huelgas iniciadas en el mes o año anterior."


def norm(texto: object) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(t.upper().split())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def indicador_de(encabezado: str) -> str | None:
    t = norm(encabezado)
    if t.startswith("HUELGAS"):
        return "huelgas"
    if t.startswith("TRABAJADORES"):
        return "trabajadores_comprendidos"
    if t.startswith("HORAS"):
        return "horas_hombre_perdidas"
    return None


def sector_de(rotulo: str) -> str | None:
    t = norm(rotulo)
    if "MINAS" in t:
        return "mineria"
    if "MANUFACT" in t:
        return "manufactura"
    if t == "TOTAL":
        return "total_nacional"
    return None


def numero(valor: object) -> float | None:
    return float(valor) if isinstance(valor, (int, float)) and not isinstance(valor, bool) else None


def leer_c92(ws) -> list[dict]:
    """Dos bloques lado a lado: AÑO, HUELGAS, TRABAJADORES, HORAS."""
    filas = list(ws.iter_rows())
    cab = next(f for f in filas if any(c.value and norm(c.value) == "ANO" for c in f))
    bloques = []  # (col_anio, {col: indicador})
    actual = None
    for c in cab:
        if c.value in (None, ""):
            continue
        if norm(c.value) == "ANO":
            actual = (c.column, {})
            bloques.append(actual)
        elif actual and indicador_de(c.value):
            actual[1][c.column] = indicador_de(c.value)
    obs = []
    for f in filas[cab[0].row:]:
        por_col = {c.column: c for c in f}
        for col_anio, cols in bloques:
            celda_anio = por_col.get(col_anio)
            if celda_anio is None or numero(celda_anio.value) is None:
                continue
            anio = int(celda_anio.value)
            if not 1900 < anio < 2100:
                continue
            for col, ind in cols.items():
                c = por_col.get(col)
                obs.append({"anio": anio, "sector": "total_nacional", "indicador": ind,
                            "valor": numero(c.value) if c else None,
                            "valor_original": "" if c is None or c.value is None else str(c.value),
                            "hoja": ws.title, "celda": c.coordinate if c else ""})
    return obs


def leer_c93(ws) -> tuple[list[dict], list[dict]]:
    """Bloques de ocho (o cuatro) años. Solo se leen columnas con año en la fila de años:
    las columnas sueltas que la hoja repite fuera de esa fila se ignoran."""
    filas = list(ws.iter_rows())
    obs, avisos = [], []
    i = 0
    while i < len(filas):
        f = filas[i]
        if any(isinstance(c.value, str) and norm(c.value).startswith("ACTIVIDAD ECONOMICA") for c in f):
            inicios = sorted((c.column, indicador_de(c.value)) for c in f
                             if isinstance(c.value, str) and indicador_de(c.value))
            fila_anios = filas[i + 1]
            colmap = {}
            for c in fila_anios:
                v = numero(c.value)
                if v is None or not 1900 < v < 2100:
                    continue
                ind = [ind for col, ind in inicios if col <= c.column][-1]
                if (ind, int(v)) in colmap.values():
                    avisos.append({"hoja": ws.title, "celda": c.coordinate, "detalle": f"año repetido {int(v)} en {ind}"})
                    continue
                colmap[c.column] = (ind, int(v))
            k = i + 2
            while k < len(filas):
                fila = filas[k]
                textos = [c for c in fila if isinstance(c.value, str) and c.value.strip()]
                if textos and (norm(textos[0].value).startswith("ACTIVIDAD ECONOMICA") or norm(textos[0].value).startswith("FUENTE")
                               or norm(textos[0].value).startswith("CUADRO")):
                    break
                if textos:
                    sector = sector_de(textos[0].value)
                    if sector:
                        por_col = {c.column: c for c in fila}
                        for col, (ind, anio) in colmap.items():
                            c = por_col.get(col)
                            obs.append({"anio": anio, "sector": sector, "indicador": ind,
                                        "valor": numero(c.value) if c else None,
                                        "valor_original": "" if c is None or c.value is None else str(c.value),
                                        "hoja": ws.title, "celda": c.coordinate if c else "",
                                        "rotulo_mtpe": " ".join(str(textos[0].value).split())})
                k += 1
            i = k
        else:
            i += 1
    return obs, avisos


def leer_c94(ws) -> dict:
    filas = list(ws.iter_rows())
    cab = next(f for f in filas if any(isinstance(c.value, str) and norm(c.value).startswith("ACTIVIDAD ECONOMICA") for c in f))
    cols = {c.column: indicador_de(c.value) for c in cab if isinstance(c.value, str) and indicador_de(c.value)}
    res = {}
    for f in filas[cab[0].row:]:
        textos = [c for c in f if isinstance(c.value, str) and c.value.strip()]
        if not textos:
            continue
        sector = sector_de(textos[0].value)
        if sector and sector not in res:
            por_col = {c.column: c for c in f}
            res[sector] = {ind: numero(por_col[col].value) for col, ind in cols.items() if col in por_col}
    return res


def leer_maestra(root: Path) -> dict:
    """Valores de la base del artículo para controles: (anio, sector, indicador) -> valor."""
    res = {}
    with (root / "bases/maestra/cruce_anio_sector_largo.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            for ind in INDICADORES:
                res[(int(r["anio"]), r["categoria_homologada_agregada"], ind)] = float(r[ind])
    with (root / "bases/reportes/resumen_ejecutivo_anual.csv").open(encoding="utf-8-sig", newline="") as f:
        nombres = {"huelgas": "huelgas_total", "trabajadores_comprendidos": "trabajadores_total",
                   "horas_hombre_perdidas": "horas_total"}
        for r in csv.DictReader(f):
            for ind, col in nombres.items():
                if r[col] != "":
                    res[(int(r["anio"]), "total_nacional", ind)] = float(r[col])
    return res


def escribir(path: Path, filas: list[dict], campos: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root
    fuente = root / FUENTE
    wb = openpyxl.load_workbook(fuente, data_only=True)
    huella = sha256(fuente)

    c92 = leer_c92(wb["C-92"])
    c93, avisos = leer_c93(wb["C-93"])
    c94 = leer_c94(wb["C-94"])
    maestra = leer_maestra(root)

    # Serie: total desde C-92 (1970-2025); minería y manufactura desde C-93 (1990-2025).
    serie = []
    for o in c92 + [o for o in c93 if o["sector"] != "total_nacional"]:
        notas = []
        if o["sector"] == "mineria":
            notas.append(NOTA_MINERIA)
        if o["indicador"] == "horas_hombre_perdidas":
            notas.append(NOTA_HHP)
        if o["sector"] == "mineria" and o["anio"] == 1996:
            notas.append("La base maestra del artículo separa petróleo y gas natural en 1996 "
                         "(minería sin petróleo: 17 huelgas, 3.794 trabajadores, 495.904 horas-hombre).")
        serie.append({**{k: o[k] for k in ("anio", "sector", "indicador", "valor", "valor_original")},
                      "fuente_archivo": FUENTE.as_posix(), "fuente_hoja": o["hoja"], "fuente_celda": o["celda"],
                      "sha256": huella, "nota": " ".join(notas)})
    serie.sort(key=lambda r: (r["anio"], SECTORES.index(r["sector"]), INDICADORES.index(r["indicador"])))
    claves = [(r["anio"], r["sector"], r["indicador"]) for r in serie]
    if len(claves) != len(set(claves)):
        print("ERROR: observaciones duplicadas", file=sys.stderr)
        return 1

    # Controles
    controles = []
    def control(tipo, anio, sector, ind, observado, referencia, fuente_ref, resultado=None):
        if resultado is None:
            if observado is None or referencia is None:
                resultado = "no_evaluable"
            else:
                resultado = "coincide" if abs(observado - referencia) < 0.5 else "difiere"
        controles.append({"control": tipo, "anio": anio, "sector": sector, "indicador": ind,
                          "valor_serie": observado, "valor_referencia": referencia,
                          "referencia": fuente_ref, "resultado": resultado})

    v92 = {(o["anio"], o["indicador"]): o["valor"] for o in c92}
    v93 = {(o["anio"], o["sector"], o["indicador"]): o["valor"] for o in c93}
    for (anio, sector, ind), val in sorted(v93.items()):
        if sector == "total_nacional":
            control("total_c93_vs_c92", anio, sector, ind, val, v92.get((anio, ind)), "C-92")
    for anio in range(1994, 2026):
        for sector in SECTORES:
            for ind in INDICADORES:
                obs = v92.get((anio, ind)) if sector == "total_nacional" else v93.get((anio, sector, ind))
                ref = maestra.get((anio, sector, ind))
                resultado = None
                if sector == "mineria" and obs is not None and ref is not None and abs(obs - ref) >= 0.5:
                    petroleo = maestra.get((anio, "explotacion_de_petroleo_y_gas_natural", ind))
                    if petroleo is not None and abs(obs - ref - petroleo) < 0.5:
                        resultado = "coincide_sumando_petroleo"
                control("serie_vs_base_articulo", anio, sector, ind, obs, ref,
                        "bases/maestra/cruce_anio_sector_largo.csv" if sector != "total_nacional"
                        else "bases/reportes/resumen_ejecutivo_anual.csv", resultado)
    for sector in SECTORES:
        for ind in INDICADORES:
            obs = v92.get((2025, ind)) if sector == "total_nacional" else v93.get((2025, sector, ind))
            control("2025_vs_c94", 2025, sector, ind, obs, c94.get(sector, {}).get(ind), "C-94")

    # Formato ancho con participaciones
    ancho = {}
    for r in serie:
        ancho.setdefault(r["anio"], {"anio": r["anio"]})[f"{r['sector']}_{r['indicador']}"] = r["valor"]
    for fila in ancho.values():
        for sector in ("mineria", "manufactura"):
            for ind in INDICADORES:
                num, den = fila.get(f"{sector}_{ind}"), fila.get(f"total_nacional_{ind}")
                fila[f"participacion_{sector}_{ind}_pct"] = round(100 * num / den, 2) if num is not None and den else None
    campos_ancho = ["anio"] + [f"{s}_{i}" for s in SECTORES for i in INDICADORES] + \
                   [f"participacion_{s}_{i}_pct" for s in ("mineria", "manufactura") for i in INDICADORES]

    out = root / SALIDA
    escribir(out / "serie_huelgas_sectores_1970_2025.csv", serie,
             ["anio", "sector", "indicador", "valor", "valor_original", "fuente_archivo", "fuente_hoja",
              "fuente_celda", "sha256", "nota"])
    escribir(out / "serie_huelgas_sectores_ancho_1970_2025.csv",
             [ancho[a] for a in sorted(ancho)], campos_ancho)
    escribir(out / "controles_huelgas_sectores.csv", controles,
             ["control", "anio", "sector", "indicador", "valor_serie", "valor_referencia", "referencia", "resultado"])

    conteo = {}
    for c in controles:
        conteo[c["resultado"]] = conteo.get(c["resultado"], 0) + 1
    resumen = {
        "fuente": FUENTE.as_posix(), "sha256": huella,
        "total_nacional": "1970-2025 (C-92)", "mineria_y_manufactura": "1990-2025 (C-93)",
        "observaciones": len(serie), "controles": conteo,
        "columnas_repetidas_ignoradas_c93": len(avisos),
        "diferencias_sin_explicar": [c for c in controles if c["resultado"] == "difiere"],
    }
    (out / "resumen_validacion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "diferencias_sin_explicar"}, ensure_ascii=False, indent=2))
    if resumen["diferencias_sin_explicar"]:
        print("ERROR: hay diferencias sin explicar; revisar controles_huelgas_sectores.csv", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
