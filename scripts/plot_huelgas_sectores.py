"""Gráfico de huelgas, trabajadores comprendidos y horas-hombre perdidas:
total nacional 1970-2025 y minería y manufactura 1990-2025.

Uso, desde la raíz del proyecto (después de build_huelgas_sectores.py):
    python scripts/plot_huelgas_sectores.py
"""
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1] / "bases" / "huelgas_sectores"
out = root / "graficos"
out.mkdir(exist_ok=True)
d = pd.read_csv(root / "serie_huelgas_sectores_ancho_1970_2025.csv")

palette = {"mineria": "#28786B", "manufactura": "#B87832", "total_nacional": "#485566"}
labels = {"mineria": "Minas y canteras", "manufactura": "Manufactura", "total_nacional": "Total nacional"}
indicadores = [
    ("huelgas", "huelgas", "Número de huelgas", 1),
    ("trabajadores_comprendidos", "trabajadores", "Miles de trabajadores", 1e3),
    ("horas_hombre_perdidas", "horas-hombre perdidas", "Millones de horas-hombre", 1e6),
]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})

fig, axs = plt.subplots(2, 3, figsize=(15, 8.5))
for j, (ind, titulo, unidad, escala) in enumerate(indicadores):
    ax = axs[0, j]
    g = d.dropna(subset=[f"total_nacional_{ind}"])
    ax.plot(g.anio, g[f"total_nacional_{ind}"] / escala, color=palette["total_nacional"], lw=2)
    ax.set_title(f"Total nacional: {titulo}", loc="left", fontweight="bold", fontsize=10.5)
    ax.set_xticks([1970, 1980, 1990, 2000, 2010, 2025])

    ax = axs[1, j]
    for sector in ("mineria", "manufactura"):
        g = d.dropna(subset=[f"{sector}_{ind}"])
        ax.plot(g.anio, g[f"{sector}_{ind}"] / escala, color=palette[sector], lw=2, label=labels[sector])
    ax.set_title(f"Minería y manufactura: {titulo}", loc="left", fontweight="bold", fontsize=10.5)
    ax.set_xticks([1990, 2000, 2010, 2020, 2025])
    ax.legend(frameon=False, fontsize=9)

for ax, (_, _, unidad, _) in zip(axs.flat, indicadores * 2):
    ax.set_ylabel(unidad)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=.2)

fig.suptitle("Huelgas en el Perú: total nacional (1970–2025), minería y manufactura (1990–2025)", fontsize=15)
fig.text(.05, .02,
         "Fuente: MTPE, Anuario Estadístico Sectorial 2025, cuadros 92 (total nacional) y 93 (actividad económica). "
         "Los paneles tienen escalas verticales distintas.\n"
         "Minería corresponde a explotación de minas y canteras e incluye petróleo y gas natural; no equivale a minería "
         "metálica y puede excluir contratistas clasificados en otras actividades.\n"
         "Las horas-hombre pueden incluir huelgas iniciadas en el mes o año anterior. En 2025, administración pública "
         "concentra el 78% de las horas-hombre perdidas (cuadro 94).",
         fontsize=8.5)
fig.tight_layout(rect=(0, .09, 1, .95))
fig.savefig(out / "huelgas_sectores_1970_2025.png", dpi=180)
print(out / "huelgas_sectores_1970_2025.png")
