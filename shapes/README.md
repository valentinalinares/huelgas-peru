# Shapes para mapas

Esta carpeta contiene las capas geograficas minimas necesarias para los mapas del proyecto.

## Archivos incluidos

- `peru_territorios_huelga.geojson`: capa regional adaptada al lenguaje territorial de la base de huelgas
- `peru_territorios_huelga_lima_total.geojson`: la misma capa, pero colapsando `lima`, `lima_metropolitana` y `lima_provincia` en `lima_total` para mapas de series largas
- `peru_provincias.geojson`: capa provincial para trabajo posterior con zonas o correspondencias mas finas
- `equivalencias_territorio_mapa.csv`: tabla de apoyo para entender como se construyo la capa territorial

Las dos capas GeoJSON fueron simplificadas para visualizacion web y notebooks. No reemplazan una cartografia oficial de alta precision.

## Criterio usado

La capa principal para mapas del proyecto es `peru_territorios_huelga.geojson`.

Si el objetivo es comparar visualmente toda la serie en el tiempo, conviene usar `peru_territorios_huelga_lima_total.geojson`.

Esa capa:

- parte de un shapefile distrital de Peru disponible localmente en `../data/`
- agrega distritos hasta formar unidades comparables con el modulo `territorio`
- separa `lima_metropolitana` de `lima_provincia`
- mantiene `callao` como unidad propia

La version `lima_total`:

- colapsa `lima`, `lima_metropolitana` y `lima_provincia`
- esta pensada para mapas temporales
- debe leerse solo como una decision cartografica, no como reemplazo de la variable original

## Salvedad metodologica

La capa geografica ayuda a visualizar la base, pero no resuelve por si sola las ambiguedades historicas del modulo `territorio`.

En particular:

- los anos viejos incluyen categorias historicas como `lima`
- la fuente mezcla nivel `regional` y nivel `zona`
- no todas las categorias antiguas tienen una equivalencia espacial perfecta en una geografia contemporanea

## Reproducir

Si existe la carpeta `../data/` con el shapefile fuente, se puede regenerar esta carpeta con:

```bash
python scripts/build_shapes.py
```
