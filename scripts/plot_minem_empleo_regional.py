"""Grafica las cinco regiones con mayor empleo minero promedio en 2025."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "minem_empleo_regional"


def main():
    data = pd.read_csv(OUT / "empleo_minero_departamental_promedio_2020_2026.csv")
    full = data[(data["anio"] <= 2025) & (data["departamento_id"] != "total_nacional")]
    top = full[full["anio"] == 2025].nlargest(5, "empleo_promedio_publicado")["departamento_id"].tolist()
    plot = full[full["departamento_id"].isin(top)]
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for department, group in plot.groupby("departamento_id"):
        ax.plot(group["anio"], group["empleo_promedio_publicado"], marker="o", lw=2, label=department.replace("_", " ").title())
    ax.set(title="Empleo minero promedio en las cinco regiones líderes de 2025", xlabel="Año", ylabel="Trabajadores")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "empleo_minero_regiones_lideres_2020_2025.png", dpi=180)
    plt.close(fig)
    print("OK: gráfico generado.")


if __name__ == "__main__":
    main()
