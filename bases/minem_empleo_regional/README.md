# Empleo minero regional — fuente sectorial MINEM

Módulo externo separado de las estadísticas del MTPE. Fuente oficial: [MINEM, Empleo Minero](https://www.gob.pe/institucion/minem/informes-publicaciones/4291678-empleo-minero), archivo `Empleo 2020 - a Agosto 2026`, consultado el 5 de noviembre de 2026.

## Cobertura

- 25 departamentos y total nacional.
- Datos mensuales completos de enero de 2020 a diciembre de 2025.
- Datos preliminares de enero a agosto de 2026.
- 2.080 observaciones mensuales y 182 promedios publicados/recalculados.

La fuente se basa en la Declaración Estadística Mensual (ESTAMIN) reportada por titulares mineros. Incluye empleo directo del subsector minero y no debe concatenarse con `explotación de minas y canteras` del MTPE: cambian la institución, el universo, la clasificación y el tratamiento de contratistas.

## Archivos

- `empleo_minero_departamental_mensual_2020_2026.csv`
- `empleo_minero_departamental_promedio_2020_2026.csv`
- `controles.csv`
- `empleo_minero_regiones_lideres_2020_2025.png`

Cada registro conserva el archivo, hoja, celda y huella SHA-256. Los 182 promedios se recalculan desde los meses disponibles; 2026 es enero–agosto y no se compara como año completo.
