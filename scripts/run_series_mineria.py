"""Reconstruye las series laborales de minería, manufactura y total nacional
a partir de los anuarios del MTPE, en el orden que exigen sus dependencias.

El inventario va primero porque extract_negociacion_cruces_historicos.py lo usa
para elegir los cuadros fuente. Los anuarios deben estar en anuarios/<año>/
(ver scripts/download_anuarios.py). La base del artículo de huelgas se
reconstruye aparte con scripts/run_publication_pipeline.py.

Uso, desde la raíz del proyecto:
    python scripts/run_series_mineria.py                  # todo
    python scripts/run_series_mineria.py --solo planilla  # un módulo
    python scripts/run_series_mineria.py --sin-graficos
    python scripts/run_series_mineria.py --lista
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTARIO = ROOT / "bases/inventario_anuarios/inventario_cuadros_1993_2025.csv"

# (módulo, script, es_grafico)
PASOS = [
    ("inventario", "build_inventario_anuarios.py", False),
    ("negociacion", "extract_negociacion_colectiva_c56.py", False),
    ("negociacion", "extract_negociacion_complementos.py", False),
    ("negociacion", "extract_negociacion_cruces_historicos.py", False),
    ("negociacion", "extract_convenios_supraregionales.py", False),
    ("negociacion", "plot_negociacion_colectiva.py", True),
    ("planilla", "extract_planilla_historica.py", False),
    ("planilla", "validate_planilla_historica.py", False),
    ("planilla", "plot_planilla_historica.py", True),
    ("planilla", "extract_planilla_puente_2002_2007.py", False),
    ("planilla", "validate_planilla_puente_2002_2007.py", False),
    ("planilla", "plot_planilla_puente_2002_2007.py", True),
    ("registros", "extract_registros_sindicales.py", False),
    ("registros", "validate_registros_sindicales.py", False),
    ("registros", "plot_registros_sindicales.py", True),
    ("huelgas", "build_huelgas_sectores.py", False),
    ("huelgas", "plot_huelgas_sectores.py", True),
    ("minem", "extract_minem_empleo_regional.py", False),
    ("minem", "validate_minem_empleo_regional.py", False),
    ("minem", "plot_minem_empleo_regional.py", True),
]
MODULOS = list(dict.fromkeys(m for m, _, _ in PASOS))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo", choices=MODULOS, action="append", help="correr solo este módulo (se puede repetir)")
    parser.add_argument("--sin-graficos", action="store_true", help="omitir los scripts de gráficos")
    parser.add_argument("--lista", action="store_true", help="mostrar el orden de ejecución y salir")
    args = parser.parse_args()

    pasos = [p for p in PASOS if not args.solo or p[0] in args.solo]
    if args.sin_graficos:
        pasos = [p for p in pasos if not p[2]]
    # Los cruces de negociación necesitan el inventario.
    if any(p[1] == "extract_negociacion_cruces_historicos.py" for p in pasos) \
            and not any(p[0] == "inventario" for p in pasos) and not INVENTARIO.exists():
        pasos.insert(0, PASOS[0])

    if args.lista:
        for i, (modulo, script, _) in enumerate(pasos, 1):
            print(f"{i:2d}. [{modulo}] scripts/{script}")
        return 0

    inicio_total = time.time()
    for i, (modulo, script, _) in enumerate(pasos, 1):
        print(f"\n== {i}/{len(pasos)} [{modulo}] {script}", flush=True)
        inicio = time.time()
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)
        if r.returncode != 0:
            print(f"\nFALLÓ scripts/{script} (código {r.returncode}). Se detiene la ejecución.", file=sys.stderr)
            return r.returncode
        print(f"   ok ({time.time() - inicio:.1f} s)")
    print(f"\nListo: {len(pasos)} pasos en {time.time() - inicio_total:.1f} s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
