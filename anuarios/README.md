# Carpeta de fuentes

Esta carpeta existe solo para que el pipeline tenga una ruta esperada para los anuarios originales.

No subir los archivos fuente al repositorio.

La estructura esperada es:

```text
anuarios/
  1993/
  1994/
  ...
  2024/
```

Cada subcarpeta debe contener los archivos originales del anuario de huelgas usados por los scripts de `scripts/`.

## Descarga reproducible

La carpeta ya incluye un scraper funcional del portal oficial de anuarios del MTPE.

Ese script:

- entra a la página índice oficial
- detecta los enlaces por año
- resuelve las páginas intermedias de `gob.pe` cuando el portal no da el ZIP directo
- descarga los `.zip`
- los descomprime dentro de `anuarios/<año>/`
- genera además un `manifest.generated.csv` con lo que encontró

Ese `manifest.generated.csv` funciona como inventario automático de las URLs detectadas en el portal para `1993-2024`.

## Archivos incluidos

- `scripts/download_anuarios.py`: scraper + descargador automático
- `manifest.generated.csv`: se genera automáticamente al correr el script

## Uso

Ejecutar:

```bash
python scripts/download_anuarios.py
```

Si quieres solo ver qué descargaría:

```bash
python scripts/download_anuarios.py --dry-run
```

Si ya existen archivos y quieres sobrescribirlos:

```bash
python scripts/download_anuarios.py --overwrite
```

Si quieres bajar solo algunos años:

```bash
python scripts/download_anuarios.py --years 2021 2022 2023 2024
```

Si usas `--years`, el script filtra solo la descarga, pero mantiene `manifest.generated.csv` con el inventario completo detectado en el portal.

## Alcance y salvedades

Este scraper:

- sí depende del portal oficial, pero ya incorpora el patrón mixto real del sitio
- maneja años con ZIP directo y años con página intermedia en `gob.pe`
- deja un `manifest.generated.csv` para trazabilidad de las URLs usadas

Si en el futuro el portal cambia de estructura, habría que ajustar este script.
