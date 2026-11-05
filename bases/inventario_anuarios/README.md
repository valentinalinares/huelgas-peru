# Inventario de anuarios MTPE, 1993–2025

Este módulo cataloga las fuentes originales sin modificarlas. Permite localizar
rápidamente un cuadro, comprobar la cobertura anual y detectar errores de
lectura o duplicados antes de construir una serie.

## Productos

- `inventario_archivos_1993_2025.csv`: un registro por archivo, con ubicación,
  tamaño, SHA-256, tema probable y resultado de lectura.
- `inventario_cuadros_1993_2025.csv`: un registro por hoja de Excel, con nombre,
  dimensiones, código de cuadro cuando se identifica y extracto del encabezado.
- `resumen_anual_1993_2025.csv`: cobertura agregada por año.
- `controles_inventario.csv`: controles explícitos de presencia, lectura y
  duplicación.
- `resumen_inventario.json`: cifras de control de la ejecución.

## Alcance y decisiones

- Se cubren las 33 carpetas anuales, de 1993 a 2025, y los archivos ZIP
  originales conservados en `_zips_originales`.
- Los siete archivos de 1993 son documentos Word antiguos y por eso no generan
  registros en el inventario de hojas. Permanecen catalogados en el inventario
  de archivos.
- En 2018 y 2019 el portal reutilizó el nombre `Cuadros.zip`. Las copias
  `Cuadros (1).zip` y `Cuadros (2).zip` son idénticas; el duplicado se conserva y
  se marca, no se elimina.
- El tema y el código de cuadro se infieren a partir del nombre del archivo, de
  la hoja y de sus primeras filas. Son ayudas de búsqueda; el contenido original
  sigue siendo la autoridad.

## Reproducción

Desde la raíz del proyecto:

```powershell
python scripts/build_inventario_anuarios.py
```

El script utiliza lectura no destructiva: `xlrd` para `.xls`, XML interno para
`.xlsx/.xlsm`, `pypdf` para PDF y la biblioteca estándar para ZIP, DOC y huellas
SHA-256.
