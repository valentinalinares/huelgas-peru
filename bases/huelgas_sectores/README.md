# Huelgas en minería, manufactura y total nacional, 1970–2025

Serie construida desde los cuadros retrospectivos del Anuario Estadístico Sectorial 2025 del MTPE (capítulo 4). Complementa la base maestra del artículo, que no se modifica.

## Cobertura

| Serie | Años | Cuadro |
|---|---|---|
| Total nacional | 1970–2025 | C-92 |
| Minería (explotación de minas y canteras) | 1990–2025 | C-93 |
| Manufactura | 1990–2025 | C-93 |

Indicadores: huelgas, trabajadores comprendidos y horas-hombre perdidas.

## Archivos

- `serie_huelgas_sectores_1970_2025.csv`: formato largo, con hoja, celda y huella SHA-256 del archivo fuente.
- `serie_huelgas_sectores_ancho_1970_2025.csv`: una fila por año, con la participación de minería y manufactura en el total.
- `controles_huelgas_sectores.csv` y `resumen_validacion.json`: controles y resumen.
- `graficos/huelgas_sectores_1970_2025.png`: total nacional desde 1970 y minería y manufactura desde 1990.

## Controles

Hay 405 controles: 402 coinciden y 3 coinciden al sumar petróleo y gas natural (ver abajo).

- El total del C-93 coincide con el C-92 en todos los años de 1990 a 2025.
- Minería, manufactura y total coinciden con la base del artículo en 1994–2025, salvo minería en 1996.
- Los valores de 2025 coinciden con el C-94.

## Diferencias con la base del artículo

- **1996.** La base maestra separa "explotación de petróleo y gas natural" (9 huelgas, 7.970 trabajadores y 168.788 horas-hombre). El MTPE los incluye en minas y canteras, igual que en los demás años. Esta serie sigue al MTPE: 26 huelgas, 11.764 trabajadores y 664.692 horas-hombre. La base del artículo registra 17, 3.794 y 495.904, y no se cambió.
- **1990–1993.** No están en la base maestra, que excluye 1993 por falta de Excel fuente. Aquí vienen del C-93 del Anuario 2025.
- **1970–1989.** Solo hay total nacional.

## Cautelas

- Minas y canteras incluye petróleo y gas natural, no equivale a minería metálica y puede excluir personal de contratistas clasificado en otras actividades.
- Las horas-hombre pueden incluir huelgas iniciadas en el mes o año anterior. En 2025 el C-95 marca esas horas con asterisco: en enero, minería registra 44.760 horas-hombre sin huelgas nuevas en el sector.
- Los valores vienen de la retrospectiva del Anuario 2025. Antes de 1994 todavía no se compararon con las cifras publicadas en cada anuario de la época.
- En el C-93 algunas filas repiten valores en columnas fuera de la fila de años. El script lee solo las columnas que tienen año.

## Reproducción

Desde la raíz del proyecto:

```bash
python scripts/build_huelgas_sectores.py
python scripts/plot_huelgas_sectores.py
```

O, con el resto de módulos: `python scripts/run_series_mineria.py --solo huelgas`.
