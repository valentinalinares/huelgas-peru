from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

PIPELINE = [
    "extract_era1_huelgas_1994_1995.py",
    "extract_era2_huelgas_1996_1999.py",
    "extract_era2_huelgas_2000_2003.py",
    "extract_era2_huelgas_2004_2020.py",
    "extract_era3_huelgas.py",
    "build_master_outputs_1993_2024.py",
]


def main() -> None:
    for script_name in PIPELINE:
        script_path = SCRIPTS / script_name
        print(f"[pipeline] Ejecutando {script_name}")
        subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(ROOT))
    print("[pipeline] Pipeline completo")


if __name__ == "__main__":
    main()
