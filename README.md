# Huelgas Perú 1993-2024

Repositorio de procesamiento, homologación y análisis de los anuarios de huelgas del MTPE para Perú.

## Qué hace este proyecto

Este proyecto construye una base longitudinal homologada de huelgas para `1993-2024` a partir de los anuarios oficiales del MTPE.

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
  2024/
```

respetando la estructura usada durante el procesamiento.

## Productos principales

En `bases/maestra/` están:

- `huelgas_modulos_maestra_1993_2024.csv`
- `huelgas_maestra_1993_2024.xlsx`
- `diccionario_idioma_comun_1993_2024.csv`
- `resumen_idioma_comun_modulos.csv`
- `tabla_lenguaje_comun_categorias.csv`
- `huelgas_legalidad_1996_2024_largo.csv`
- `huelgas_legalidad_1996_2024_resumen_anual.csv`
- `verificacion_calificacion_1993_2024_resumen.csv`
- cruces por `año x sector`
- cruces por `año x territorio regional`
- gráficos exportados

En `bases/cruce_sector_territorio/` está:

- `sector_territorio_2001_2024.csv`
- `validacion_sector_territorio_2001_2024.csv`
- `validacion_sector_territorio_resumen.csv`
- `cobertura_sector_territorio_1993_2024.csv`

En `bases/mapas_folium/` están:

- `01_huelgas_territorio_tiempo.html`
- `02_trabajadores_territorio_tiempo.html`
- `03_horas_hombre_territorio_tiempo.html`
- `04_mineria_territorio_tiempo.html`

En `bases/reportes/` están:

- `resumen_ejecutivo_anual.csv`
- `resumen_region_anual.csv`
- `resumen_region_sector_dominante_2001_2024.csv`

## Cobertura real

- `1993`: excluido de la base tabular porque solo existe en `.DOC`
- `1994-1995`: años parciales
- `1996-2024`: años homologados con módulos completos

## Cobertura por producto

No todos los productos del repositorio cubren exactamente el mismo rango:

- **base maestra principal**: `1993-2024`
- **módulos completos comparables**: `1996-2024`
- **mapas territoriales comparables**: `1999-2024`
- **cruce complementario `sector x territorio`**: `2001-2024`

Esto no significa que la base maestra empiece en `2001`. Lo que empieza en `2001` es la base complementaria del cuadro cruzado `actividad x territorio`.

La razón es esta:

- la base maestra se construye a partir de módulos simples anuales y sí cubre `1993-2024` con las salvedades de `1993-1995`
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

## Límites importantes

- `territorio` mezcla nivel regional y nivel zona en la fuente; por eso se usa con advertencia de `estructura_mixta`
- la serie de `Lima` cambia históricamente en la fuente: en años viejos aparece `lima`, luego `lima_provincia` y luego `lima_metropolitana`; no deben leerse como tres territorios simultáneos equivalentes
- los mapas del notebook `03` usan una decisión cartográfica adicional: `lima`, `lima_metropolitana` y `lima_provincia` se colapsan en `lima_total` solo para visualización
- los mapas territoriales comparables empiezan en `1999`, no porque falten años en la base maestra, sino porque `1996-1998` todavía usan regiones históricas no equivalentes 1 a 1 con la capa geográfica contemporánea
- en varios años la fuente aclara que las `horas_hombre_perdidas` incluyen horas generadas por huelgas provenientes del `mes anterior`; en `2024` incluso aparece la fórmula `año y/o mes anterior`, por lo que ese indicador no siempre corresponde solo al período inmediato del cuadro
- varios anuarios aluden a `sector privado` en el título, pero los cuadros incluyen categorías como `administracion publica y defensa`, `ensenanza` y `servicios sociales y de salud`
- eso no se trató como un error del pipeline, sino como una inconsistencia conceptual de la propia fuente oficial
- por eso `administracion publica y defensa` se conservó y se homologó a `adm_publica`; no se eliminó ni se forzó artificialmente a `sector privado`
- no existe cruce observado `legalidad x sector`
- no existe cruce observado `legalidad x territorio`
- la base maestra principal no incluye `sector x territorio`; ese cruce quedó separado como base complementaria y hoy está disponible para `2001-2024`, con validación propia y algunos años marcados `revisar`
- la base complementaria `sector x territorio` no reemplaza a la base maestra: solo amplía los cruces observables donde el cuadro cruzado existe

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
- `docs/checklist_publicacion.md`
