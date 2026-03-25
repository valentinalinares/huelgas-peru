# Diccionario de variables

## Base maestra

Archivo principal:

- `bases/maestra/huelgas_modulos_maestra_1993_2024.csv`

## Variables

- `anio`: año del anuario
- `modulo`: dimensión temática del cuadro
- `hoja_excel`: hoja original del workbook fuente
- `categoria_original`: texto exacto observado en la fuente
- `categoria_homologada_fina`: traducción fina, conservando el mayor detalle posible
- `categoria_homologada_agregada`: traducción comparable longitudinalmente
- `regla_homologacion`: explicación breve de la traducción aplicada
- `nivel_territorial`: `regional` o `zona`, solo para territorio
- `territorio_padre`: región madre de una zona, solo para territorio
- `huelgas`: número absoluto de huelgas
- `pct_huelgas`: porcentaje de huelgas dentro del cuadro fuente
- `trabajadores_comprendidos`: número absoluto de trabajadores
- `pct_trabajadores`: porcentaje de trabajadores dentro del cuadro fuente
- `horas_hombre_perdidas`: número absoluto de horas-hombre
- `pct_horas`: porcentaje de horas-hombre dentro del cuadro fuente
- `flag_hhp_arrastre`: marca notas metodológicas de arrastre de horas-hombre
- `flag_faltante_fuente`: marca faltantes declarados por la fuente
- `flag_paro_nacional_registrado_lima`: marca casos anotados en Lima por la fuente
- `nota_fuente`: concatenación de notas metodológicas del cuadro original
- `archivo_homologado`: workbook anual ya procesado
- `carpeta_bloque`: bloque de procesamiento al que pertenece el año
- `tipo_anio`: `excluido_sin_excel_fuente`, `parcial` o `completo`

## Bases auxiliares

- `huelgas_legalidad_1996_2024_largo.csv`: legalidad por año en formato largo
- `huelgas_legalidad_1996_2024_resumen_anual.csv`: resumen anual de legalidad
- `verificacion_calificacion_1993_2024_resumen.csv`: verificación de consistencia del módulo de calificación
- `cruce_anio_sector_largo.csv`: cruce observable `año x sector`
- `cruce_anio_territorio_regional_largo.csv`: cruce observable `año x territorio regional`
