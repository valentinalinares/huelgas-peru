"""Grafica empleo y cobertura de negociación en los cortes de junio 2002–2007."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "planilla_electronica"


def main():
    data = pd.read_csv(OUT / "resumen_puente_junio_2002_2007.csv")
    labels = {"mineria": "Minería", "manufactura": "Manufactura", "total_nacional": "Total nacional"}
    colors = {"mineria": "#e67e22", "manufactura": "#2878b5", "total_nacional": "#2ca02c"}
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for sector, group in data.groupby("sector_id"):
        axes[0].plot(group["anio"], group["trabajadores"], marker="o", lw=2, color=colors[sector], label=labels[sector])
        axes[1].plot(group["anio"], group["tasa_sujetos_negociacion"] * 100, marker="o", lw=2, color=colors[sector], label=labels[sector])
    axes[0].set(title="Trabajadores, corte de junio", xlabel="Año", ylabel="Trabajadores")
    axes[1].set(title="Trabajadores sujetos a negociación / trabajadores", xlabel="Año", ylabel="Porcentaje")
    axes[0].legend(frameon=False)
    fig.suptitle("Hoja de Resumen de Planillas, 2002–2007\nSector privado, empresas de 5 o más trabajadores", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "puente_planillas_junio_2002_2007.png", dpi=180)
    plt.close(fig)
    print("OK: gráfico generado.")


if __name__ == "__main__":
    main()
