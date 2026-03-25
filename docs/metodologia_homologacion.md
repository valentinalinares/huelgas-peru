# Metodología de homologación

## Objetivo

Construir una base longitudinal comparable de huelgas para Perú a partir de anuarios oficiales con layouts cambiantes entre `1993` y `2024`.

## Qué consigue la homologación

La homologación traduce cada anuario a un idioma común para poder comparar años distintos aun cuando cambian:

- numeración de hojas
- nombres de categorías
- desagregación de tramos
- estructura territorial
- diseño interno del cuadro

## Universo temporal

- `1993`: excluido del pipeline tabular, porque solo existe en `.DOC`
- `1994-1995`: años parciales
- `1996-2024`: años homologados en formato tabular

## Eras

### Era 1: 1994-1995

- años parciales
- actividad, causas, organización y territorio
- no hay `calificacion`, `tamano` ni `duracion`

### Era 2 vieja: 1996-2003

- misma lógica general de módulos
- layouts más variables
- requiere parsers específicos por bloque o por año

### Era 2 estable: 2004-2020

- estructura muy estable
- módulos comparables con reglas ya cerradas

### Era 3: 2021-2024

- mismos módulos que la era estable
- cambia la numeración de hojas dentro del anuario

## Módulos del idioma común

- `actividad`
- `territorio`
- `causas`
- `calificacion`
- `organizacion`
- `tamano`
- `duracion`

## Fase 2 complementaria

Además de la base maestra principal, el proyecto incluye una extracción separada del cuadro cruzado `actividad x territorio`.

- no entra a la base principal porque no existe para toda la serie
- se publica como base complementaria en `bases/cruce_sector_territorio/`
- en el estado actual cubre `2001-2024`
- su validación se reporta por separado

## Reglas centrales

### Calificación

Se homologa a dos categorías:

- `procedente`
- `ilegal`

### Tamaño

Se preserva el detalle fino cuando existe, pero la agregación longitudinal usa:

- `20_49`
- `50_99`
- `100_199`
- `200_299`
- `300_mas`

### Duración

Se preserva el detalle fino cuando existe, pero la agregación longitudinal usa:

- `1_dia`
- `2_3_dias`
- `4_7_dias`
- `8_15_dias`
- `16_mas_dias`

### Territorio

Se distingue entre:

- `nivel_territorial = regional`
- `nivel_territorial = zona`

No se colapsan ambos niveles en una sola suma, porque la fuente reporta los dos.

## Validación

Cada módulo fue validado contra el total fuente del anuario.

En `calificacion`, para todos los años con módulo disponible, se verificó que:

- `procedente + ilegal` en `huelgas` coincide con el total fuente
- `procedente + ilegal` en `trabajadores_comprendidos` coincide con el total fuente
- `procedente + ilegal` en `horas_hombre_perdidas` coincide con el total fuente
