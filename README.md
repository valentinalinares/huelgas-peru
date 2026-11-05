# Huelgas Perú 1993-2025

Repositorio de procesamiento, homologación y análisis de los anuarios de huelgas del MTPE para Perú.

## Artículo asociado

Este repositorio documenta y permite reproducir el procesamiento de datos desarrollado para el artículo:

> Manky, Omar y Durga V. Linares Herrera. 2026. “Huelgas masivas sin institucionalización: Perú, 1994–2025”. *Estudios Sociológicos de El Colegio de México*, 44: 1–27. [https://doi.org/10.24201/es.2026v44.e3114](https://doi.org/10.24201/es.2026v44.e3114).

El artículo fue publicado el 21 de octubre de 2026 y está disponible en la [página de *Estudios Sociológicos*](https://estudiossociologicos.colmex.mx/index.php/es/es/article/view/3114).

## Qué hace este proyecto

Este proyecto construye una base longitudinal homologada de huelgas para `1993-2025` a partir de los anuarios oficiales del MTPE.

El resultado principal es una base maestra donde cada año fue traducido a un idioma común para poder comparar:

- actividad económica
- territorio
- causas
- calificación de la huelga
- organización sindical
- tamaño
- duración

## Qué contiene

- `scripts/`: extractores y consolidadores
- `notebooks/`: procesamiento narrado, análisis, mapas interactivos y exploración del cruce sector-territorio
- `bases/maestra/`: outputs finales ya generados
- `bases/negociacion_colectiva/`: serie histórica del cuadro C-56 del MTPE para 1995-2025
- `bases/inventario_anuarios/`: catálogo reproducible de 544 archivos y 8.155 hojas/cuadros de los anuarios 1993–2025
- `bases/planilla_electronica/`: empleo, sindicalizados y remuneraciones (2008–2025), intermediación (2009–2025) y tercerización (2011–2025), para minería, manufactura y total nacional privado
- `bases/huelgas_sectores/`: huelgas, trabajadores comprendidos y horas-hombre perdidas del total nacional (1970–2025) y de minería y manufactura (1990–2025), desde los cuadros retrospectivos del Anuario 2025
- `bases/cruce_sector_territorio/`: extracción complementaria del cuadro cruzado `actividad x territorio`
- `bases/reportes/`: tablas de reporte ejecutivo para consulta rápida
- `shapes/`: capas geográficas preparadas para mapas
- `docs/`: metodología, variables y limitaciones
- `anuarios/`: carpeta esperada para los archivos fuente originales, no versionados

## Qué NO se sube

Los anuarios originales del MTPE no están incluidos en el repositorio. Para reproducir el pipeline hay que colocarlos localmente en:

```text
anuarios/
  1993/
  1994/
  ...
  2025/
```

respetando la estructura usada durante el procesamiento.

## Productos principales

En `bases/maestra/` están:

- `huelgas_modulos_maestra_1993_2025.csv`
- `huelgas_maestra_1993_2025.xlsx`
- `diccionario_idioma_comun_1993_2025.csv`
- `resumen_idioma_comun_modulos.csv`
- `tabla_lenguaje_comun_categorias.csv`
- `huelgas_legalidad_1996_2025_largo.csv`
- `huelgas_legalidad_1996_2025_resumen_anual.csv`
- `verificacion_calificacion_1993_2025_resumen.csv`
- cruces por `año x sector`
- cruces por `año x territorio regional`
- gráficos exportados

En `bases/cruce_sector_territorio/` está:

- `sector_territorio_2001_2025.csv`
- `validacion_sector_territorio_2001_2025.csv`
- `validacion_sector_territorio_resumen.csv`
- `cobertura_sector_territorio_1993_2025.csv`

En `bases/mapas_folium/` están:

- `01_huelgas_territorio_tiempo.html`
- `02_trabajadores_territorio_tiempo.html`
- `03_horas_hombre_territorio_tiempo.html`
- `04_mineria_territorio_tiempo.html`

En `bases/reportes/` están:

- `resumen_ejecutivo_anual.csv`
- `resumen_region_anual.csv`
- `resumen_region_sector_dominante_2001_2025.csv`

En `bases/negociacion_colectiva/` están:

- `base_negociacion_colectiva_c56_1995_2025.csv`: base larga con las 15 actividades y el total nacional
- `serie_mineria_manufactura_total_1995_2025.csv`: comparación anual de minas y canteras, manufactura y total nacional
- `validacion_c56_2024_vs_2025.csv`: auditoría de los 480 valores comunes entre ambos anuarios
- `NOTA_METODOLOGICA.md`: criterios, fuente y precauciones de comparabilidad
- `complementos/`: etapas nacionales (1997–2025), laudos (1993–2025) y cruces por actividad con etapas y organizaciones (1995–2025), con celdas fuente y controles. Los cuadros anuales confirman 8/5 arbitrajes en 1998/1999 frente a 7/4 laudos; ambas series se conservan como indicadores distintos.
- `graficos/`: evolución de los convenios y etapas de solución en 2025.

La ampliación de negociación colectiva se desarrolló posteriormente al artículo citado; no forma parte de sus insumos originales. Los cruces complementarios sectoriales de etapas y organizaciones cubren 1995–2025 y preservan los símbolos originales sin convertirlos automáticamente en cero.

La ampliación posterior de Planilla Electrónica contiene bases mensuales y anuales, tasa de sindicalización, celdas fuente, inventario con huellas de archivos, controles y gráficos. Para sindicalización y remuneraciones, 2008–2011 conserva promedios publicados; desde 2012 se calculan medias simples de doce meses. Las remuneraciones están en soles nominales. Véase `bases/planilla_electronica/README.md` para límites y una diferencia de dos trabajadores en el total de sindicalizados de junio de 2015. Los cortes de junio de 2002–2007 se incorporaron como puente separado, no como prolongación homogénea.

## Cobertura real

- `1993`: excluido de la base tabular porque solo existe en `.DOC`
- `1994-1995`: años parciales
- `1996-2025`: años homologados con módulos completos

## Cobertura por producto

No todos los productos del repositorio cubren exactamente el mismo rango:

- **base maestra principal**: `1993-2025`
- **módulos completos comparables**: `1996-2025`
- **mapas territoriales comparables**: `1999-2025`
- **cruce complementario `sector x territorio`**: `2001-2025`

Esto no significa que la base maestra empiece en `2001`. Lo que empieza en `2001` es la base complementaria del cuadro cruzado `actividad x territorio`.

La razón es esta:

- la base maestra se construye a partir de módulos simples anuales y sí cubre `1993-2025` con las salvedades de `1993-1995`
- los mapas territoriales comparables arrancan en `1999` porque `1996-1998` todavía usan regiones históricas no equivalentes 1 a 1 con la geografía contemporánea
- el cruce `sector x territorio` arranca en `2001` porque ese cuadro cruzado no está disponible o no es homogéneo antes de ese año

## Reproducir

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Si quieres poblar `anuarios/` automáticamente desde el portal oficial:

```bash
python scripts/download_anuarios.py
```

Ejecutar los extractores:

```bash
python scripts/run_publication_pipeline.py
```

O seguir el pipeline documentado en:

- `notebooks/01_procesamiento_homologacion.ipynb`
- `notebooks/02_analisis_base_maestra.ipynb`
- `notebooks/03_mapas_interactivos.ipynb`
- `notebooks/04_cruce_sector_territorio.ipynb`
- `notebooks/05_reporte_ejecutivo.ipynb`

Si quieres reconstruir también la base complementaria del cuadro cruzado:

```bash
python scripts/extract_sector_territorio_phase2.py
```

Para reconstruir en orden todas las series laborales de minería, manufactura y total nacional (inventario, negociación colectiva, Planilla Electrónica, registros sindicales, huelgas por sector y MINEM):

```bash
python scripts/run_series_mineria.py
```

Con `--lista` muestra el orden de ejecución, con `--solo <módulo>` corre un módulo y con `--sin-graficos` omite las figuras. El inventario debe correr antes que los cruces de negociación, porque estos lo usan para elegir los cuadros fuente. Los bloques siguientes muestran los mismos pasos uno por uno.

Para reconstruir la serie de negociación colectiva del cuadro C-56:

```bash
python scripts/extract_negociacion_colectiva_c56.py
```

Para extraer los complementos y reproducir los gráficos (requiere el inventario de anuarios):

```bash
python scripts/build_inventario_anuarios.py
python scripts/extract_negociacion_complementos.py
python scripts/extract_negociacion_cruces_historicos.py
python scripts/plot_negociacion_colectiva.py
```

Para reconstruir el inventario detallado de anuarios:

```bash
python scripts/build_inventario_anuarios.py
```

Para reconstruir, validar y graficar las series de Planilla Electrónica:

```bash
python scripts/extract_planilla_historica.py
python scripts/validate_planilla_historica.py
python scripts/plot_planilla_historica.py
python scripts/extract_planilla_puente_2002_2007.py
python scripts/validate_planilla_puente_2002_2007.py
python scripts/plot_planilla_puente_2002_2007.py
```

Para reconstruir, validar y graficar las series de Registro Sindical:

```bash
python scripts/extract_registros_sindicales.py
python scripts/validate_registros_sindicales.py
python scripts/plot_registros_sindicales.py
```

Para reconstruir y graficar la serie de huelgas por sector (total desde 1970; minería y manufactura desde 1990):

```bash
python scripts/build_huelgas_sectores.py
python scripts/plot_huelgas_sectores.py
```

Para reconstruir, validar y graficar el módulo externo MINEM de empleo minero regional:

```bash
python scripts/extract_minem_empleo_regional.py
python scripts/validate_minem_empleo_regional.py
python scripts/plot_minem_empleo_regional.py
```

## Límites importantes

- `territorio` mezcla nivel regional y nivel zona en la fuente; por eso se usa con advertencia de `estructura_mixta`
- la serie de `Lima` cambia históricamente en la fuente: en años viejos aparece `lima`, luego `lima_provincia` y luego `lima_metropolitana`; no deben leerse como tres territorios simultáneos equivalentes
- los mapas del notebook `03` usan una decisión cartográfica adicional: `lima`, `lima_metropolitana` y `lima_provincia` se colapsan en `lima_total` solo para visualización
- los mapas territoriales comparables empiezan en `1999`, no porque falten años en la base maestra, sino porque `1996-1998` todavía usan regiones históricas no equivalentes 1 a 1 con la capa geográfica contemporánea
- en varios años la fuente aclara que las `horas_hombre_perdidas` incluyen horas generadas por huelgas provenientes del `mes anterior`; en `2024` y `2025` aparece arrastre desde el año y/o mes anterior, por lo que ese indicador no siempre corresponde solo al período inmediato del cuadro
- varios anuarios aluden a `sector privado` en el título, pero los cuadros incluyen categorías como `administracion publica y defensa`, `ensenanza` y `servicios sociales y de salud`
- eso no se trató como un error del pipeline, sino como una inconsistencia conceptual de la propia fuente oficial
- por eso `administracion publica y defensa` se conservó y se homologó a `adm_publica`; no se eliminó ni se forzó artificialmente a `sector privado`
- no existe cruce observado `legalidad x sector`
- no existe cruce observado `legalidad x territorio`
- la base maestra principal no incluye `sector x territorio`; ese cruce quedó separado como base complementaria y hoy está disponible para `2001-2025`, con validación propia y algunos años marcados `revisar`
- la base complementaria `sector x territorio` no reemplaza a la base maestra: solo amplía los cruces observables donde el cuadro cruzado existe
- en negociación colectiva, la categoría `explotación de minas y canteras` no equivale exactamente a minería metálica y puede omitir contratistas clasificados en otras actividades
- el MTPE indica que el dato de negociación colectiva de `2025` incluye convenios solucionados en `2019-2024` cuya vigencia comprende 2025; no debe interpretarse automáticamente como convenios nuevos firmados durante 2025
- los registros sindicales son flujos administrativos y no equivalen al stock de sindicatos activos; el único stock nacional hallado en estos anuarios corresponde a `2002` y se conserva en una base separada
- en Registro Sindical, el cuadro por actividad del Anuario `2008` suma `203` sindicatos, mientras la serie retrospectiva del Anuario `2025` informa `201`; ambos valores se preservan y la diferencia queda marcada en los controles
- en Registro Sindical, `explotación de minas y canteras` tampoco equivale exactamente a minería metálica y puede omitir contratistas clasificados en otras actividades
- las Hojas de Resumen de Planillas de `2002-2007` son cortes de junio para empresas privadas de 5 o más trabajadores; se publican como puente separado y no como prolongación homogénea de Planilla Electrónica `2008-2025`
- en ese puente, trabajadores sujetos a negociación colectiva no equivale necesariamente a trabajadores sindicalizados, e ingreso promedio no equivale a la remuneración promedio posterior
- la fuente de `2007` cambia el cálculo del ingreso promedio y excluye ingresos superiores a 200 mil; la ruptura se conserva en los controles
- el módulo regional MINEM `2020-2026` usa ESTAMIN y empleo directo del subsector minero; se mantiene separado de MTPE porque no comparte exactamente universo, clasificación ni tratamiento de contratistas
- el dato MINEM de `2026` solo cubre enero-agosto y es preliminar; no debe compararse como año completo con 2020-2025

## Sobre los HTML de mapas

Los mapas `folium` exportados en `bases/mapas_folium/` sí se pueden compartir como archivos `.html` y abrir en un navegador.

Salvedad técnica:

- funcionan bien si quien los abre tiene internet, porque el HTML carga librerías web de `leaflet` y `folium` desde CDN
- si la persona abre el archivo completamente offline, el mapa puede no renderizar bien

En otras palabras:

- **HTML + navegador + internet**: sí, debería abrir y funcionar
- **solo HTML, sin internet**: no es completamente portable en su estado actual

## Documentación

- `docs/metodologia_homologacion.md`
- `docs/diccionario_variables.md`
- `docs/limitaciones_fuente.md`
- `bases/maestra/nota_sector_publico_privado.md`
- `docs/nota_horas_hombre_arrastre.md`
- `docs/actualizacion_huelgas_2025_articulo.md`
- `docs/nota_metodologica_sintesis_mineria_mtpe_2025.md`
- `docs/checklist_publicacion.md`
