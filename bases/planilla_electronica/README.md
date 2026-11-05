# Planilla Electrónica: minería, manufactura y total nacional privado

Primera versión de las series históricas. Fuente: capítulos de Planilla Electrónica de los anuarios del MTPE, ediciones 2008–2025. Esta ampliación es posterior al artículo de huelgas publicado.

## Cobertura recuperada

| Indicador | Serie anual | Datos de origen |
|---|---|---|
| Empleo | 2008–2025 | Doce meses de cada año |
| Trabajadores sindicalizados | 2008–2025 | Promedio publicado 2008–2011; doce meses desde 2012 |
| Trabajadores en empresas de intermediación laboral | 2009–2025 | Doce meses de cada año |
| Trabajadores en empresas de tercerización | 2011–2025 | Doce meses de cada año |
| Remuneración promedio | 2008–2025 | Promedio publicado 2008–2011; doce promedios mensuales desde 2012 |

Cada serie contiene minería (explotación de minas y canteras), manufactura (industrias manufactureras) y total nacional **del sector privado registrado**. El total no representa todo el empleo peruano ni incorpora por sí mismo el sector informal o el público.

Hay 2.808 observaciones mensuales y 258 observaciones anuales. Los datos mensuales seleccionados están completos: cada promedio calculado usa doce valores. Las ausencias de intermediación en 2008 y tercerización en 2008–2010 no se convierten en ceros.

## Archivos

- `base_mensual.csv`: observaciones originales seleccionadas, con año, mes, sector, indicador, valor original, unidad, archivo, hoja, cuadro y celda.
- `base_anual.csv`: promedios anuales; identifica si se calcularon a partir de los doce meses o se tomaron del promedio publicado. `mes=0` identifica el registro anual, no un mes del calendario. `meses_disponibles` queda vacío en promedios publicados sin extracción mensual.
- `resumen_anual.csv`: vista por año y sector de los cinco indicadores y la tasa de sindicalización. Para análisis de comparabilidad, consultar también `base_anual.csv`.
- `inventario_fuentes.csv`: los 86 pares año–indicador utilizados, títulos de cuadro, notas originales y huella SHA-256 de los 18 archivos fuente.
- `cobertura.csv`: 90 combinaciones de año e indicador, incluidas las cuatro todavía no identificadas.
- `controles.csv`: 1.288 comprobaciones de agregación y coherencia.
- `graficos/`: dos figuras descriptivas reproducibles.

## Construcción e interpretación

1. Se seleccionan cuadros por su contenido y ámbito. No se usa la posición de minería en la tabla: las actividades cambian de orden. Las hojas de Lima Metropolitana se excluyen de estas series nacionales.
2. Los nombres de hoja y los números impresos del cuadro se guardan por separado: no siempre coinciden. Por ejemplo, en 2014 empleo nacional está en la hoja `C-52`, pero su título dice cuadro 51.
3. Los indicadores mensuales se resumen con **promedio simple de enero a diciembre**. No se suman trabajadores a lo largo del año, porque eso no produciría personas únicas.
4. Para 2008–2011 se conserva el subtotal publicado de trabajadores sindicalizados y el total promedio mensual publicado de remuneraciones. No se les atribuyen doce datos mensuales que no se extrajeron. Se marca el cambio de método/origen en 2012.
5. La remuneración anual desde 2012 es la media simple de los doce promedios mensuales. No equivale a ingreso anual individual, remuneración real ni media ponderada anual de personas. Se conserva la precisión original; los gráficos y resúmenes pueden redondear para presentación.
6. Para la remuneración nacional se utiliza el **promedio general publicado** de cada mes. No se suman los promedios sectoriales ni se calcula una media simple entre actividades.
7. La tasa de sindicalización es `100 × promedio de sindicalizados / promedio de empleo`, por año y sector. No se presenta como promedio simple de tasas mensuales. Para 2008–2011 se verificó que el empleo promedio del cuadro de sindicalización coincida con el promedio calculado del cuadro mensual.
8. Intermediación y tercerización se conservan como variables distintas. Los cuadros clasifican trabajadores en empresas por actividad registrada: no permiten identificar necesariamente el sector de la empresa usuaria, ni todo el personal contratista que trabaja en una mina. No se suman al empleo ni se asume que sean categorías mutuamente excluyentes.
9. Se preservan las categorías y advertencias originales. `Explotación de minas y canteras` no equivale exactamente a minería metálica. No se interpreta automáticamente una variación como cambio económico real sin revisar cobertura y definiciones.

## Controles y observaciones de la fuente

- **1.274 controles coinciden**, trece sumas coinciden aunque contienen componentes sin dato numérico y un control presenta diferencia.
- **Junio de 2015, sindicalizados:** la suma de actividades es 195.977 y el total publicado es 195.979. Se conserva 195.979 en la base y se registra una diferencia de −2 en el archivo de controles. No se reasigna a ninguna actividad.
- **Intermediación 2025:** enseñanza tiene celdas vacías en los doce meses. La suma de los valores numéricos coincide con el total, pero esto no demuestra que las celdas vacías sean ceros. Ninguna de las tres series seleccionadas está vacía.
- **Sindicalización 2008:** existe un componente no numérico fuera de las tres filas seleccionadas; la suma numérica coincide con el total dentro de tolerancia de precisión.
- Los 504 pares mensuales de sindicalizados y empleo disponibles desde 2012 cumplen que sindicalizados no supera empleo.
- Las notas de las fuentes cambian de Planillas Electrónicas a PDT 0601 / T-Registro y PLAME. Se conservaron en el inventario; falta una revisión específica de definiciones, cobertura y eventuales revisiones retrospectivas.

## Puente histórico 2002–2007

Se extrajo un bloque separado de las Hojas de Resumen de Planillas: 54 observaciones para empleo, ingreso promedio y trabajadores sujetos a negociación colectiva, con minería, manufactura y total nacional. Los productos son `puente_junio_2002_2007.csv`, `resumen_puente_junio_2002_2007.csv`, `controles_puente_junio_2002_2007.csv`, `inventario_puente_junio_2002_2007.csv`, `cobertura_puente_junio_2002_2007.csv` y `puente_planillas_junio_2002_2007.png`.

Este bloque **no se concatena como si fuera la misma serie** que Planilla Electrónica 2008–2025: es un corte de junio, cubre empresas privadas de 5 o más trabajadores y usa ingreso promedio, no la remuneración promedio posterior. Los trabajadores sujetos a negociación colectiva tampoco equivalen necesariamente a trabajadores sindicalizados.

En 2007 la fuente cambia el cálculo del ingreso promedio y la hoja utilizada indica la eliminación de ingresos superiores a 200 mil. Por ello los promedios publicados de 2007 se conservan con salvedad metodológica y no se fuerzan a coincidir con una media ponderada basada en todos los trabajadores.

## Límites de esta versión

La revisión de 1994–2001 no encontró una serie nacional por actividad comparable
con las Hojas de Resumen de Planillas que comienzan en 2002. Esos capítulos se
concentran en colocaciones, formación laboral, cierres y autorizaciones; los
pocos cuadros de PEA corresponden a Lima Metropolitana. La evidencia se detalla
en `nota_pre_2002_y_region.md`.

Por tanto, 2008 es el comienzo recuperado de la base de Planilla Electrónica y
2002 el comienzo del puente de planillas, **no una afirmación de que antes no
existan estadísticas laborales de ningún tipo**. La intermediación comparable
comienza en 2009 y la tercerización en 2011; las ausencias anteriores no se
convierten en cero. El empleo minero regional se resolvió mediante un módulo
externo MINEM 2020–2026, mantenido separado por universo y definición.

Los datos corresponden a cada edición anual de origen. No se han reemplazado por posibles revisiones en ediciones posteriores.

## Reproducción

Desde la raíz del proyecto, con las dependencias del repositorio instaladas:

```text
python scripts/extract_planilla_historica.py
python scripts/validate_planilla_historica.py
python scripts/plot_planilla_historica.py
python scripts/extract_planilla_puente_2002_2007.py
python scripts/validate_planilla_puente_2002_2007.py
python scripts/plot_planilla_puente_2002_2007.py
```

Los originales se leen sin modificarlos. El validador contrasta cada dato extraído con su celda fuente y vuelve a calcular los promedios anuales y tasas.
