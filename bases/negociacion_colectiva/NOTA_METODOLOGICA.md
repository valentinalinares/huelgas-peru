# Negociación colectiva — cuadro C-56 del MTPE

## Alcance de esta primera base

La base reconstruye el cuadro `C-56` del capítulo 2 del **Anuario Estadístico Sectorial 2025 del MTPE**. Contiene el número de convenios colectivos solucionados–registrados por actividad económica para **1995–2025**.

Se conservan las 15 actividades económicas publicadas y el total nacional. Para el análisis solicitado se genera además una serie comparativa de:

- explotación de minas y canteras;
- industrias manufactureras;
- total nacional.

## Archivos

- `base_negociacion_colectiva_c56_1995_2025.csv`: base larga, una fila por año y actividad.
- `serie_mineria_manufactura_total_1995_2025.csv`: serie anual comparativa en formato ancho.
- `validacion_c56_2024_vs_2025.csv`: comparación celda por celda del período 1995–2024 entre los anuarios 2024 y 2025.
- `resumen_validacion.json`: controles automáticos y valores principales.

Todos los CSV están codificados como UTF-8 con firma para conservar las tildes al abrirlos en Excel.

## Criterios de limpieza y validación

1. Se extraen los dos bloques de años del cuadro C-56 y se normalizan abreviaturas y espacios de los rótulos. Las tildes del archivo original se conservan; su visualización defectuosa en algunas salidas de consola no implica daño en la fuente.
2. Se mantiene el rótulo original del MTPE en una columna separada para trazabilidad.
3. Cada observación identifica el archivo fuente, año del anuario, hoja y cuadro.
4. Se comprueba que no existan duplicados por año–actividad ni valores negativos o faltantes.
5. Se verifica que la suma de las 15 actividades coincida con el total nacional publicado en cada uno de los 31 años.
6. Se comparan los 480 valores comunes de 1995–2024 con el cuadro C-56 del Anuario 2024 para detectar revisiones históricas.

## Precauciones de interpretación

- La categoría **“Explotación de minas y canteras”** no equivale exactamente a minería metálica. Algunos trabajadores de contratistas mineros pueden estar clasificados en otras actividades económicas.
- El MTPE señala que el dato de **2025** incluye convenios solucionados en 2019–2024 cuya vigencia comprende 2025. Por ello no debe interpretarse automáticamente como convenios nuevos firmados durante 2025 ni compararse como una variación homogénea sin considerar esta nota.
- El cuadro también incluye pliegos de reclamos presentados en años anteriores y solucionados a la fecha.

## Reproducción

Ejecutar desde la carpeta del proyecto:

```powershell
python scripts/extract_negociacion_colectiva_c56.py
```

El programa vuelve a leer los anuarios originales, reconstruye los tres CSV y detiene la ejecución si falla alguna validación.

## Ampliación del capítulo 2

La carpeta `complementos/` contiene etapas de solución nacionales 1997–2025,
laudos por actividad y designación 1993–2025, y cruces por actividad con etapa
de solución y organización para 1995–2025. Su `README.md` documenta coberturas,
celdas fuente, símbolos y diferencias entre arbitrajes y laudos. La carpeta
`graficos/` presenta cuatro figuras reproducibles de convenios, etapas y tipos
de organización; se genera con `python scripts/plot_negociacion_colectiva.py`.
