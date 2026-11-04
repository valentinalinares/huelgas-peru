"""Genera gráficos descriptivos de Registro Sindical."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bases" / "registros_sindicales"


def main():
    private = pd.read_csv(OUT / "registros_privados_anual.csv")
    activity = pd.read_csv(OUT / "sindicatos_privados_actividad_anual.csv")
    focus = activity[activity["sector_analitico"].isin(["mineria", "manufactura", "total_nacional"])].copy()
    labels = {"mineria": "Minería", "manufactura": "Manufactura", "total_nacional": "Total nacional"}

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.plot(private["anio"], private["registros_sindicatos"], color="#1f4e79", lw=2, label="Nuevos sindicatos")
    ax.plot(private["anio"], private["cancelaciones_registro_sindical"], color="#b44b4b", lw=2, label="Cancelaciones")
    ax.set(title="Sector privado: registros y cancelaciones sindicales, 1993–2025", xlabel="Año", ylabel="Número")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "registros_y_cancelaciones_1993_2025.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    for key, group in focus.groupby("sector_analitico"):
        ax.plot(group["anio"], group["total_publicado"], lw=2, marker="o" if key != "total_nacional" else None, ms=3, label=labels[key])
    ax.set(title="Nuevos sindicatos privados por actividad, 2002–2025", xlabel="Año", ylabel="Sindicatos registrados")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "sindicatos_por_actividad_2002_2025.png", dpi=180)
    plt.close(fig)
    print("OK: 2 gráficos generados.")


if __name__ == "__main__":
    main()
