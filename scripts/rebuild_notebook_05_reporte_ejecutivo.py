from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "05_reporte_ejecutivo.ipynb"


def md(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata.language_info = {"name": "python"}

nb.cells = [
    md(
        """# 05. Reporte ejecutivo

Este cuaderno construye un reporte de acceso rápido para responder preguntas simples sobre la serie:

- cuántas huelgas hubo por año
- qué proporción fue ilegal
- en qué sector se concentraron más
- en qué territorio se concentraron más
- qué regiones concentraron más huelgas por año
- cuál fue el sector dominante dentro de cada región cuando existe el cruce `sector x territorio`
"""
    ),
    code(
        """from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().resolve()
if (ROOT / 'bases').exists() and (ROOT / 'notebooks').exists():
    project_root = ROOT
else:
    project_root = ROOT.parent

REPORTES = project_root / 'bases' / 'reportes'
SCRIPTS = project_root / 'scripts'

if not (REPORTES / 'resumen_ejecutivo_anual.csv').exists():
    import subprocess, sys
    subprocess.run([sys.executable, str(SCRIPTS / 'build_executive_report_outputs.py')], check=True, cwd=project_root)

resumen_anual = pd.read_csv(REPORTES / 'resumen_ejecutivo_anual.csv')
resumen_region = pd.read_csv(REPORTES / 'resumen_region_anual.csv')
resumen_region_sector = pd.read_csv(REPORTES / 'resumen_region_sector_dominante_2001_2024.csv')
"""
    ),
    md("## Resumen anual ejecutivo"),
    code("resumen_anual.head(10)"),
    code(
        """fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(resumen_anual['anio'], resumen_anual['huelgas_total'], marker='o')
ax.set_title('Huelgas totales por año')
ax.set_xlabel('Año')
ax.set_ylabel('Huelgas')
ax.grid(alpha=0.2)
plt.show()
"""
    ),
    code(
        """legalidad = resumen_anual[resumen_anual['pct_ilegal_huelgas'].notna()].copy()
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(legalidad['anio'], legalidad['pct_ilegal_huelgas'] * 100, marker='o', color='#b22222')
ax.set_title('Porcentaje de huelgas ilegales por año')
ax.set_xlabel('Año')
ax.set_ylabel('% ilegal')
ax.grid(alpha=0.2)
plt.show()
"""
    ),
    md(
        """## Sector y territorio principal por año

La tabla siguiente sirve como vista ejecutiva compacta de cada año.
"""
    ),
    code(
        """columnas = [
    'anio',
    'huelgas_total',
    'pct_ilegal_huelgas',
    'sector_principal_huelgas',
    'sector_principal_huelgas_valor',
    'territorio_principal_huelgas',
    'territorio_principal_huelgas_valor',
]
vista = resumen_anual[columnas].copy()
vista['pct_ilegal_huelgas'] = (vista['pct_ilegal_huelgas'] * 100).round(2)
vista
"""
    ),
    md("## Regiones con más huelgas en la serie"),
    code(
        """top_regiones = (
    resumen_region.groupby('region', as_index=False)['huelgas']
    .sum()
    .sort_values('huelgas', ascending=False)
    .head(10)
)
top_regiones
"""
    ),
    code(
        """top_regiones_lista = top_regiones['region'].tolist()
serie_top = resumen_region[resumen_region['region'].isin(top_regiones_lista)].copy()
pivot_top = serie_top.pivot(index='anio', columns='region', values='huelgas').fillna(0)

fig, ax = plt.subplots(figsize=(14, 6))
for col in pivot_top.columns:
    ax.plot(pivot_top.index, pivot_top[col], marker='o', linewidth=1.5, label=col)
ax.set_title('Top regiones por huelgas a lo largo del tiempo')
ax.set_xlabel('Año')
ax.set_ylabel('Huelgas')
ax.grid(alpha=0.2)
ax.legend(ncol=2, fontsize=8)
plt.show()
"""
    ),
    md(
        """## Tabla regional por año

Aquí puedes cambiar `anio_objetivo` para ver el detalle exacto de un año.
"""
    ),
    code(
        """anio_objetivo = 2024
tabla_region_anio = (
    resumen_region[resumen_region['anio'] == anio_objetivo]
    .sort_values(['huelgas', 'trabajadores_comprendidos'], ascending=False)
    [['anio', 'region', 'huelgas', 'participacion_huelgas_anual', 'trabajadores_comprendidos', 'horas_hombre_perdidas', 'rank_region_huelgas']]
    .copy()
)
tabla_region_anio['participacion_huelgas_anual'] = (tabla_region_anio['participacion_huelgas_anual'] * 100).round(2)
tabla_region_anio
"""
    ),
    md(
        """## Sector dominante dentro de cada región

Este bloque usa la base complementaria `sector x territorio`, por lo que cubre `2001-2024`.
"""
    ),
    code("resumen_region_sector.head(10)"),
    code(
        """anio_region_objetivo = 2024
tabla_sector_region = (
    resumen_region_sector[resumen_region_sector['anio'] == anio_region_objetivo]
    .sort_values(['sector_principal_huelgas', 'huelgas_region_total'], ascending=False)
    [['anio', 'region', 'sector_principal_region', 'sector_principal_huelgas', 'participacion_sector_principal_huelgas', 'huelgas_region_total']]
    .copy()
)
tabla_sector_region['participacion_sector_principal_huelgas'] = (tabla_sector_region['participacion_sector_principal_huelgas'] * 100).round(2)
tabla_sector_region
"""
    ),
    md(
        """## Archivos exportados

Este notebook se apoya en tres tablas que quedan listas para consulta o exportación:

- `bases/reportes/resumen_ejecutivo_anual.csv`
- `bases/reportes/resumen_region_anual.csv`
- `bases/reportes/resumen_region_sector_dominante_2001_2024.csv`
"""
    ),
]

nbf.write(nb, NOTEBOOK)
print(f"Notebook rebuilt: {NOTEBOOK}")
