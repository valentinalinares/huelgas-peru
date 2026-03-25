# Checklist de publicacion

Antes de subir el repositorio a GitHub, revisar esto:

- confirmar que `anuarios/` no incluya carpetas por año en el commit
- confirmar que `anuarios/README.md` y `anuarios/manifest.generated.csv` si queden visibles
- confirmar que `bases/maestra/` y `bases/cruce_sector_territorio/` contengan los outputs finales
- confirmar que `bases/reportes/` contenga las tablas ejecutivas si se quiere publicar esa capa de salida
- decidir si `bases/mapas_folium/` se va a subir o si se dejará solo para compartir por Drive
- confirmar que `notebooks/` solo tenga los cuadernos numerados:
  - `01_procesamiento_homologacion.ipynb`
  - `02_analisis_base_maestra.ipynb`
  - `03_mapas_interactivos.ipynb`
  - `04_cruce_sector_territorio.ipynb`
  - `05_reporte_ejecutivo.ipynb`
- decidir si `03_mapas_interactivos.ipynb` se sube con outputs pesados o si se limpia antes del commit
- confirmar que `scripts/download_anuarios.py` corre
- confirmar que `scripts/run_publication_pipeline.py` corre
- confirmar que `scripts/extract_sector_territorio_phase2.py` corre
- confirmar que `README.md` y `docs/` describan el estado real del repo

Comandos utiles antes de subir:

```bash
python scripts/download_anuarios.py --dry-run
python scripts/run_publication_pipeline.py
python scripts/extract_sector_territorio_phase2.py
```

Que no deberia subirse:

- archivos originales descargados en `anuarios/<anio>/`
- entornos virtuales
- caches de Python
- checkpoints de notebooks

Que es opcional subir:

- `bases/mapas_folium/*.html`: útiles para compartir, pero pesan bastante
- `03_mapas_interactivos.ipynb` con outputs embebidos: funciona bien localmente, pero hace pesado el repositorio
