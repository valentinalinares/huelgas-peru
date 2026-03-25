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
- `notebooks/`: procesamiento narrado, análisis y un cuaderno base para mapas
- `bases/maestra/`: outputs finales ya generados
- `bases/cruce_sector_territorio/`: extracción complementaria del cuadro cruzado `actividad x territorio`
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

## Cobertura real

- `1993`: excluido de la base tabular porque solo existe en `.DOC`
- `1994-1995`: años parciales
- `1996-2024`: años homologados con módulos completos

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
- `notebooks/04_cruce_sector_territorio.ipynb`

Si quieres reconstruir también la base complementaria del cuadro cruzado:

```bash
python scripts/extract_sector_territorio_phase2.py
```

## Límites importantes

- `territorio` mezcla nivel regional y nivel zona en la fuente; por eso se usa con advertencia de `estructura_mixta`
- la serie de `Lima` cambia históricamente en la fuente: en años viejos aparece `lima`, luego `lima_provincia` y luego `lima_metropolitana`; no deben leerse como tres territorios simultáneos equivalentes
- en varios años la fuente aclara que las `horas_hombre_perdidas` incluyen horas generadas por huelgas provenientes del `mes anterior`; en `2024` incluso aparece la fórmula `año y/o mes anterior`, por lo que ese indicador no siempre corresponde solo al período inmediato del cuadro
- no existe cruce observado `legalidad x sector`
- no existe cruce observado `legalidad x territorio`
- la base maestra principal no incluye `sector x territorio`; ese cruce quedó separado como base complementaria y hoy está disponible para `2001-2024`, con validación propia y algunos años marcados `revisar`

## Documentación

- `docs/metodologia_homologacion.md`
- `docs/diccionario_variables.md`
- `docs/limitaciones_fuente.md`
- `docs/nota_horas_hombre_arrastre.md`
- `docs/checklist_publicacion.md`
