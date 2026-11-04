# Complementos de negociación colectiva

Fuente: Anuario Estadístico Sectorial MTPE 2025, capítulo 2, archivo original conservado en `anuarios/2025/`. Cada observación guarda cuadro, celda, valor original y unidad. Estas bases amplían la investigación después del artículo publicado; no se presentan como insumos utilizados en ese artículo.

## Productos y cobertura

| Archivo CSV | Contenido | Cobertura | Filas |
|---|---|---|---:|
| etapas_nacional_1997_2025 | C-50: pliegos presentados, convenios solucionados y seis etapas de solución | Nacional, 1997–2025 | 232 |
| etapas_por_actividad_2025 | C-60: etapas de solución por actividad económica | 15 actividades y total, 2025 | 128 |
| organizacion_por_actividad_2025 | C-62: tipo de organización por actividad económica | 15 actividades y total, 2025 | 128 |
| laudos_por_actividad_1993_2025 | C-68: laudos registrados por actividad | 15 actividades y total, 1993–2025 | 528 |
| laudos_designacion_1993_2025 | C-70: designación de árbitros | Nacional, 1993–2025 | 231 |
| controles_complementos | Sumas internas y comparación entre cuadros | 266 controles | 266 |
| inventario_capitulo2_2025 | Títulos y ámbito de las hojas de cuadros | 31 hojas; una contiene C-75 y C-76 | 31 |

Las categorías `total` y `Total nacional` son agregados publicados. No sumarlos junto a sus componentes. En C-50, pliegos presentados y convenios solucionados son indicadores distintos: no se suman y su cociente no es una tasa de resolución de una misma cohorte.

## Validación y observaciones

Se obtienen 264 coincidencias y dos discrepancias. Los cruces C-60 y C-62 cuadran por filas y columnas, y sus totales por actividad coinciden con C-56. Los totales de C-68 coinciden con C-70 y con la suma de actividades para los 33 años.

| Año | Arbitraje en C-50 | Laudos en C-68 y C-70 | Decisión |
|---|---:|---:|---|
| 1998 | 8 | 7 | Conservar ambos registros y marcar discrepancia |
| 1999 | 5 | 4 | Conservar ambos registros y marcar discrepancia |

Estas diferencias requieren revisar ediciones anteriores y las definiciones de registro. No se corrigen ni se fuerza la igualdad. El campo `resultado` del archivo de controles permite identificar las diferencias.

Los guiones del C-50 se conservan en `valor_original`, con `valor` vacío y estado `simbolo_fuente_sin_interpretar`. La suma de las etapas numéricas coincide con el total, pero eso no demuestra que cada guion signifique cero. La fila de autoridad administrativa aparece partida en dos líneas: se toma la línea `DE TRABAJO`, sin duplicar la categoría. No se extraen las subcategorías de árbitros de C-50, que mezclan cifras negativas y paréntesis; para ese detalle se usa C-70.

La nota de C-70 excluye a la Dirección Regional de Trabajo del Callao desde 2011. C-68 no repite esa nota, aunque sus totales coinciden: se registra la advertencia sin atribuirle una cobertura no declarada.

En C-62 se usan los encabezados de fila 8. La fila 9 contiene etiquetas auxiliares inconsistentes; por ejemplo, debajo de `SINDICATO DE OBREROS` dice `EMPLEADOS`. Las categorías conservadas corresponden al encabezado principal.

Los datos de 2025 incluyen convenios solucionados en 2019–2024 cuya vigencia comprende 2025. Las organizaciones de C-62 clasifican **convenios**, no personas sindicalizadas ni número de sindicatos. Los ceros de laudos son los publicados en el cuadro; no prueban ausencia de todo arbitraje fuera de su cobertura.

## Qué queda pendiente

- Extender hacia atrás los cruces por actividad y etapa de solución, y por actividad y organización, revisando anuarios previos. Su cobertura actual aquí es únicamente 2025.
- Verificar las diferencias de arbitraje de 1998–1999 contra fuentes anteriores.
- Buscar registros nominativos por empresa o sindicato: los cuadros extraídos son agregados y no identifican empresas o sindicatos individuales.
- Construir las series de Planilla Electrónica, registros sindicales y la actualización sectorial de huelgas conforme al memo.

## Reproducción

Desde la raíz del proyecto: `python scripts/extract_negociacion_complementos.py`.

El programa lee el original sin modificarlo, preserva los símbolos y exporta controles independientes. Las diferencias entre fuentes se notifican sin borrar años ni observaciones.
