# Nota metodológica sintética: trabajo y minería en el Perú

## 1. Alcance

Esta nota sintetiza las series sobre trabajo en minería construidas en
noviembre de 2026. El objetivo es conservar la mayor extensión histórica
disponible hasta 2025 para empleo, remuneraciones, sindicalización, negociación
colectiva y huelgas, comparando cuando es posible:

- explotación de minas y canteras;
- industrias manufactureras;
- total nacional.

Los anuarios del MTPE son la fuente principal. El módulo regional MINEM se
mantiene separado porque usa otra institución, universo y definición.

## 2. Matriz de cobertura

| Módulo / indicador | Cobertura recuperada | Periodicidad / agregación | Universo y fuente |
|---|---|---|---|
| Inventario de anuarios | 1993–2025 | 544 archivos y 8.155 hojas/cuadros | Anuarios MTPE y 33 ZIP originales |
| Convenios colectivos por actividad (C-56) | 1995–2025 | Conteo anual publicado | Nacional, MTPE |
| Etapas de solución por actividad | 1995–2025 | Conteo anual publicado | Nacional, MTPE |
| Organización sindical de los convenios | 1995–2025 | Conteo anual publicado | Nacional, MTPE |
| Pliegos y etapas nacionales (C-50) | 1997–2025 | Serie retrospectiva anual | Nacional, MTPE |
| Laudos arbitrales | 1993–2025 | Conteo anual publicado | Nacional y actividad, MTPE |
| Planillas: empleo, ingreso y negociación | 2002–2007 | Corte de junio | Empresas privadas de 5 o más trabajadores, MTPE |
| Planilla Electrónica: empleo | 2008–2025 | Promedio simple de 12 meses | Sector privado registrado, MTPE |
| Trabajadores sindicalizados | 2008–2025 | Promedio publicado 2008–2011; media simple de 12 meses desde 2012 | Sector privado registrado, MTPE |
| Intermediación laboral | 2009–2025 | Promedio simple de 12 meses | Empresas de intermediación, MTPE |
| Tercerización | 2011–2025 | Promedio simple de 12 meses | Empresas de tercerización, MTPE |
| Remuneración promedio | 2008–2025 | Promedio publicado 2008–2011; media simple de 12 promedios mensuales desde 2012 | Sector privado registrado, soles nominales, MTPE |
| Registros sindicales privados | 1993–2025 | Flujo administrativo anual | Sector privado, MTPE |
| Registros sindicales públicos | 2004–2025 | Flujo administrativo anual | Sector público/ROSSP, MTPE |
| Nuevos sindicatos privados por actividad | 2002–2025 | Suma de registros mensuales | Sector privado, MTPE |
| Organizaciones sindicales vigentes | 2002 | Stock publicado | Nacional, MTPE |
| Huelgas | 1993–2025; cobertura parcial en los primeros años | Conteos, trabajadores y horas-hombre; módulos comparables completos principalmente desde 1996 | MTPE |
| Huelgas por sector (retrospectiva) | Total 1970–2025; minería y manufactura 1990–2025 | Huelgas, trabajadores y horas-hombre publicados | MTPE, Anuario 2025, C-92 y C-93 |
| Empleo minero regional | 2020–2025 completos; enero–agosto de 2026 preliminar | Promedio de meses disponibles | ESTAMIN/MINEM, 25 departamentos y total |

## 3. Reglas de construcción

### Conservación y trazabilidad

Los originales permanecen intactos. Las bases guardan, según el módulo,
archivo, hoja, cuadro, celda o rango, rótulo original y huella SHA-256. Los
guiones, celdas vacías y otros símbolos se conservan como tales: no se
convierten automáticamente en cero. Los años antiguos no se eliminan por cambios
de formato, definición o cobertura.

### Agregación anual de Planilla Electrónica

El empleo, la intermediación, la tercerización y las remuneraciones mensuales se
resumen mediante promedio simple de enero a diciembre. No se suman trabajadores
mensuales porque eso no produciría personas únicas. La tasa de sindicalización
se calcula como:

`100 × promedio anual de trabajadores sindicalizados / promedio anual de empleo`.

No es el promedio simple de doce tasas mensuales. Para 2008–2011 se conservan
los promedios publicados cuando no se extrajeron doce valores mensuales. La
remuneración nacional usa el promedio general mensual publicado; no es una media
simple entre actividades.

### Series que no deben concatenarse

El puente de planillas 2002–2007 es un corte de junio para empresas privadas de
cinco o más trabajadores. `Ingreso promedio` no equivale a `remuneración
promedio`, y `trabajadores sujetos a negociación colectiva` no equivale
necesariamente a `trabajadores sindicalizados`. Se publica junto a Planilla
Electrónica, pero no como una prolongación homogénea.

El empleo regional MINEM tampoco se concatena con el empleo MTPE de
`explotación de minas y canteras`: ESTAMIN usa un universo minero sectorial y un
tratamiento de contratistas diferente.

## 4. Rupturas y advertencias principales

### Minería

La categoría MTPE `explotación de minas y canteras` no equivale exactamente a
minería metálica. Además, parte del personal de contratistas que trabaja en una
mina puede figurar bajo construcción, servicios, intermediación u otra actividad.
Por eso se usa como aproximación sectorial y no como conteo exhaustivo del empleo
minero.

### Negociación colectiva

El dato de 2025 incluye convenios solucionados en 2019–2024 cuya vigencia
comprende 2025. No debe leerse automáticamente como convenios nuevos firmados en
2025. Los tipos de organización clasifican convenios, no personas sindicalizadas
ni sindicatos existentes.

Los cuadros de etapas informan 8 arbitrajes en 1998 y 5 en 1999; los cuadros de
laudos registran 7 y 4. Los anuarios contemporáneos confirman los primeros
valores. Se conservan ambos indicadores porque un arbitraje y un laudo registrado
no son necesariamente la misma unidad administrativa.

En 2022 las categorías numéricas del cuadro de etapas suman 267 frente a un
total publicado de 269 y tres componentes aparecen como guion. No se imputan los
dos convenios ni se transforma el guion en cero.

### Planillas

En 2007 cambia el cálculo del ingreso promedio y la fuente excluye ingresos
superiores a 200 mil. En junio de 2015 la suma de actividades sindicalizadas es
195.977 y el total publicado 195.979; se preserva la diferencia de dos. Antes de
2002 no se encontró una serie nacional por actividad comparable: los capítulos
de empleo de 1994–2001 miden principalmente colocaciones, formación, cierres y
autorizaciones, o PEA de Lima Metropolitana.

### Registros sindicales

Los registros y cancelaciones son flujos administrativos y no el stock de
sindicatos activos. El único stock nacional identificado corresponde a 2002 y
se mantiene separado. Para 2008, el cuadro anual por actividad suma 203 nuevos
sindicatos y la retrospectiva de 2025 informa 201; ambos valores se conservan.

### Huelgas

Las horas-hombre pueden incluir arrastres de una huelga iniciada antes del mes o
año de referencia. En 2025, Ica registra cero huelgas y cero trabajadores, pero
28.136 horas-hombre provenientes de una huelga iniciada en 2024. Lima
Metropolitana incluye huelgas de ámbito nacional registradas en Lima. La
actualización a 2025 no modifica los valores comunes hasta 2024 de los cuatro
productos longitudinales centrales auditados.

En 1996 la base del artículo separa petróleo y gas natural de minas y canteras.
El MTPE los incluye, como en los demás años. Por eso la serie por sector de
`bases/huelgas_sectores/` registra 26 huelgas mineras en 1996 y la base del
artículo 17. Esa serie también extiende minería y manufactura a 1990 y el total
nacional a 1970 con los cuadros retrospectivos del Anuario 2025.

## 5. Productos y reproducción

Las bases y notas específicas están en:

- `bases/inventario_anuarios/`;
- `bases/negociacion_colectiva/`;
- `bases/planilla_electronica/`;
- `bases/registros_sindicales/`;
- `bases/maestra/` y `bases/huelgas_actualizacion_2025.md`;
- `bases/huelgas_sectores/`;
- `bases/minem_empleo_regional/`.

Cada módulo tiene rutinas de extracción, validación y/o gráficos en `scripts/`.
Para correrlas todas en orden: `python scripts/run_series_mineria.py` (con
`--lista` muestra el orden y con `--solo <módulo>` corre un módulo). El
inventario debe ir antes que los cruces de negociación, porque estos lo usan
para elegir los cuadros fuente.
El inventario permite localizar cuadros adicionales sin volver a abrir
manualmente los 511 archivos almacenados en las carpetas anuales.

## 6. Pendientes opcionales para una segunda etapa

Quedan como ampliaciones opcionales:

- extraer y homologar los listados nominativos de convenios por empresa/razón
  social identificados en 1997, 2002, 2003, 2005, 2011 y 2014–2019;
- decidir, antes del análisis econométrico, qué tramos usar ante cada ruptura;
- deflactar remuneraciones si se requiere analizar poder adquisitivo, usando una
  fuente de precios externa y una convención explícita;
- evaluar microdatos si se necesita empleo minero por región con una definición
  comparable a Planilla Electrónica.
