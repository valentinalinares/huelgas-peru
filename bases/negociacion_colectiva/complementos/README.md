# Complementos de negociación colectiva

Fuente: Anuario Estadístico Sectorial MTPE 2025, capítulo 2, archivo original conservado en `anuarios/2025/`. Cada observación guarda cuadro, celda, valor original y unidad. Estas bases amplían la investigación después del artículo publicado; no se presentan como insumos utilizados en ese artículo.

## Productos y cobertura

| Archivo CSV | Contenido | Cobertura | Filas |
|---|---|---|---:|
| etapas_nacional_1997_2025 | C-50: pliegos presentados, convenios solucionados y seis etapas de solución | Nacional, 1997–2025 | 232 |
| etapas_por_actividad_1995_2025 | Etapas de solución por actividad económica | 1995–2025 | 3.613 |
| organizacion_por_actividad_1995_2025 | Tipo de organización por actividad económica | 1995–2025 | 3.936 |
| serie_prioritaria_cruces_1995_2025 | Minería, manufactura y total para ambos cruces | 1995–2025 | 1.425 |
| inventario_cruces_historicos_1995_2025 | Fuentes, hojas, cuadros y categorías | 62 cuadros | 62 |
| controles_cruces_historicos | Sumas internas, cruces entre tablas y comparación con C-56 | 1995–2025 | 1.962 |
| laudos_por_actividad_1993_2025 | C-68: laudos registrados por actividad | 15 actividades y total, 1993–2025 | 528 |
| laudos_designacion_1993_2025 | C-70: designación de árbitros | Nacional, 1993–2025 | 231 |
| convenios_supraregionales_2013_2019 | C-40 del Anuario 2019: convenios de carácter supraregional o nacional (D.S. 017-2012-TR), excluidos del cuadro nacional en 2013–2019 | 15 actividades y total, 2013–2019 | 112 |
| convenios_con_supraregionales_2013_2019 | Minería, manufactura y total: C-56 más C-40 como suma referencial | 2013–2019 | 21 |
| controles_supraregionales | Suma de actividades y comparación con los C-40 de 2017 y 2018 | 183 controles, todos coinciden | 183 |
| controles_complementos | Sumas internas y comparación entre cuadros | 266 controles | 266 |
| inventario_capitulo2_2025 | Títulos y ámbito de las hojas de cuadros | 31 hojas; una contiene C-75 y C-76 | 31 |

Los archivos `etapas_por_actividad_2025.csv` y
`organizacion_por_actividad_2025.csv` se conservan como instantánea de la
primera extracción. Sus 128 registros coinciden fila por fila con el año 2025
de las nuevas bases históricas.

Las categorías `total` y `Total nacional` son agregados publicados. No sumarlos junto a sus componentes. En C-50, pliegos presentados y convenios solucionados son indicadores distintos: no se suman y su cociente no es una tasa de resolución de una misma cohorte.

## Validación y observaciones

La primera extracción obtiene 264 coincidencias y dos discrepancias. La
ampliación histórica agrega 1.962 controles: 1.927 coincidencias, 34 casos no
evaluables porque el total o la celda fuente es un símbolo y un control parcial
por símbolos; no hay diferencias numéricas sin explicar. Los totales por
actividad de etapas y organización coinciden entre sí y con C-56 siempre que la
fuente publica un valor numérico.

| Año | Arbitraje en C-50 | Laudos en C-68 y C-70 | Decisión |
|---|---:|---:|---|
| 1998 | 8 | 7 | Conservar ambos registros y marcar discrepancia |
| 1999 | 5 | 4 | Conservar ambos registros y marcar discrepancia |

Estas diferencias requieren revisar ediciones anteriores y las definiciones de registro. No se corrigen ni se fuerza la igualdad. El campo `resultado` del archivo de controles permite identificar las diferencias.

La revisión de los anuarios contemporáneos confirma que los cuadros anuales de
etapas por actividad registran 8 arbitrajes en 1998 (6 por acuerdo de partes y 2
por resolución directoral) y 5 en 1999 (3 y 2). Por tanto, C-50 y los cuadros
anuales coinciden; C-68/C-70 registran un laudo menos en cada año. Esto respalda
que se trata de una diferencia entre indicadores/tablas y no de un error de
transcripción. Se conservan ambas series.

En 2022, el total nacional del cuadro de etapas es 269, mientras las categorías
numéricas suman 267 y tres componentes están publicados como guion. El control
se marca `suma_parcial_por_simbolos`; los guiones no se convierten a cero ni se
imputan.

Los guiones del C-50 se conservan en `valor_original`, con `valor` vacío y estado `simbolo_fuente_sin_interpretar`. La suma de las etapas numéricas coincide con el total, pero eso no demuestra que cada guion signifique cero. La fila de autoridad administrativa aparece partida en dos líneas: se toma la línea `DE TRABAJO`, sin duplicar la categoría. No se extraen las subcategorías de árbitros de C-50, que mezclan cifras negativas y paréntesis; para ese detalle se usa C-70.

La nota de C-70 excluye a la Dirección Regional de Trabajo del Callao desde 2011. C-68 no repite esa nota, aunque sus totales coinciden: se registra la advertencia sin atribuirle una cobertura no declarada.

En C-62 se usan los encabezados de fila 8. La fila 9 contiene etiquetas auxiliares inconsistentes; por ejemplo, debajo de `SINDICATO DE OBREROS` dice `EMPLEADOS`. Las categorías conservadas corresponden al encabezado principal.

Desde 2020, cada año incluye convenios solucionados en años anteriores cuya vigencia comprende ese año, según la nota de cada anuario. Las organizaciones de C-62 clasifican **convenios**, no personas sindicalizadas ni número de sindicatos. Los ceros de laudos son los publicados en el cuadro; no prueban ausencia de todo arbitraje fuera de su cobertura.

## Registros nominativos

El inventario identificó listados de convenios por empresa/razón social en los
anuarios de 1997, 2002, 2003, 2005, 2011 y 2014–2019. Su estructura y cobertura
no son continuas y no equivalen a la serie agregada; quedan identificados para
una extracción nominativa separada, si se decide priorizarla.

## Reproducción

Desde la raíz del proyecto. El inventario va primero porque los cruces históricos lo usan para elegir los cuadros fuente:

```powershell
python scripts/build_inventario_anuarios.py
python scripts/extract_negociacion_complementos.py
python scripts/extract_negociacion_cruces_historicos.py
python scripts/extract_convenios_supraregionales.py
```

También se puede correr todo el módulo con `python scripts/run_series_mineria.py --solo negociacion`, que agrega el inventario si falta.

El programa lee el original sin modificarlo, preserva los símbolos y exporta controles independientes. Las diferencias entre fuentes se notifican sin borrar años ni observaciones.
