# Limitaciones de la fuente

## 1993

No existe workbook tabular de huelgas. Solo hay documentos `.DOC`.

## 1994-1995

Son años parciales.

No existe en la fuente:

- `calificacion`
- `tamano`
- `duracion`

## Territorio

La fuente mezcla:

- nivel regional
- nivel zona

Por eso el módulo `territorio` debe leerse con la advertencia `estructura_mixta`.

Además, la serie de Lima cambia históricamente:

- `1994-1999`: aparece `lima` como categoría histórica
- `2000-2010`: aparece `lima_provincia`
- `2011-2024`: aparece `lima_metropolitana` y `lima_provincia`

Estas etiquetas no deben leerse como tres territorios plenamente equivalentes dentro de una misma serie sin una decisión analítica adicional.

## Sector público / privado

Varios anuarios dicen `sector privado` en el título, pero incluyen categorías como:

- `administracion publica y defensa`
- `ensenanza`
- `servicios sociales y de salud`

Esto debe leerse como una limitación conceptual de la estadística oficial, no como un error de procesamiento.

## Horas-hombre perdidas

En varios años la propia fuente advierte que las `horas_hombre_perdidas` incluyen horas generadas por huelgas provenientes del `mes anterior`.

En `2024`, en al menos un cuadro, la nota es todavía más fuerte y habla de `año y/o mes anterior`.

Por eso, este indicador debe leerse como una medida oficial acumulada/reportada por el anuario, no siempre como horas generadas exclusivamente dentro del período inmediato del cuadro.

En la base homologada esto queda marcado con `flag_hhp_arrastre`.

El detalle de años y módulos afectados está en `docs/nota_horas_hombre_arrastre.md`.

## Cruces no observables con esta fuente principal

No existe, en la base principal:

- `legalidad x sector`
- `legalidad x territorio`
- `legalidad x organizacion`

El cruce `sector x territorio` no forma parte de la base maestra principal. Sin embargo, el repositorio sí incluye una extracción complementaria del cuadro `actividad x territorio` para `2001-2024`.

Esa base complementaria debe leerse con su propia validación:

- varios años quedan completamente en `ok`
- otros quedan como `ok_con_salvedad` por filas sin total absoluto en la fuente
- algunos años aún quedan `revisar` y requieren revisión adicional del cuadro cruzado
