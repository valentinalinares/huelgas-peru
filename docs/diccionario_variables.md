# Diccionario de variables

## Base maestra

Archivo principal:

- `bases/maestra/huelgas_modulos_maestra_1993_2024.csv`

Archivos de referencia del idioma comun:

- `bases/maestra/diccionario_idioma_comun_1993_2024.csv`
- `bases/maestra/resumen_idioma_comun_modulos.csv`
- `bases/maestra/tabla_lenguaje_comun_categorias.csv`

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

## Tabla canónica del lenguaje común

La referencia más útil para revisar la homologación no es solo el listado de columnas, sino esta tabla:

- `bases/maestra/tabla_lenguaje_comun_categorias.csv`

Ahí cada fila representa una categoría homologada del lenguaje común, con:

- `modulo`: variable o dimensión analítica
- `concepto`: qué mide esa variable
- `categoria_homologada_agregada`: categoría comparable longitudinalmente
- `nivel_territorial`: solo aplica a `territorio`
- `anio_min`, `anio_max`, `n_anios_observados`: rango observado en la base
- `observacion_metodologica`: nota breve sobre comparabilidad

La tabla resumida por módulo está en:

- `bases/maestra/resumen_idioma_comun_modulos.csv`

## Módulos y conceptos

| modulo | concepto |
|---|---|
| `actividad` | Rama o sector económico reportado por el anuario para clasificar las huelgas |
| `territorio` | Ubicación territorial reportada por la fuente para clasificar las huelgas |
| `causas` | Motivo resumido de la huelga según el cuadro anual de causas |
| `calificacion` | Condición legal de la huelga según la categoría jurídica usada en cada anuario |
| `organizacion` | Tipo de organización sindical o representación que convoca o sostiene la huelga |
| `tamano` | Tramo de trabajadores comprendidos por huelga según el cuadro de tamaño |
| `duracion` | Tramo de duración de la huelga según el cuadro anual de días |

## Categorías del lenguaje homologado por módulo

### `actividad`

Categorías agregadas comparables:

- `adm_publica`
- `agricultura`
- `comercio`
- `construccion`
- `electricidad_agua`
- `ensenanza`
- `explotacion_de_petroleo_y_gas_natural`
- `financiero`
- `inmobiliario`
- `manufactura`
- `mineria`
- `otros_servicios`
- `paro_nacional`
- `pesca`
- `salud_social`
- `transporte`

Nota:

- `adm_publica` se conserva porque aparece explícitamente en la fuente, aunque varios anuarios hablen de `sector privado` en el título.

### `territorio`

El módulo `territorio` tiene muchas categorías porque mezcla:

- regiones contemporáneas: `amazonas`, `ancash`, `apurimac`, `arequipa`, `ayacucho`, `cajamarca`, `callao`, `cusco`, `huancavelica`, `huanuco`, `ica`, `junin`, `la_libertad`, `lambayeque`, `lima_metropolitana`, `lima_provincia`, `loreto`, `madre_de_dios`, `moquegua`, `pasco`, `piura`, `puno`, `san_martin`, `tacna`, `tumbes`, `ucayali`
- regiones históricas: `andres_a_caceres`, `chavin`, `grau`, `inka`, `libertadores_wari`, `moquegua_tacna_puno`, `nor_oriental_del_maranon`
- zonas: `abancay`, `camana`, `canete`, `casma`, `cerro_de_pasco`, `chachapoyas`, `chiclayo`, `chimbote`, `chincha`, `huacho`, `huamachuco`, `huancayo`, `huaraz`, `ilo`, `iquitos`, `juanjui`, `juliaca`, `la_oroya`, `mollendo`, `moyobamba`, `nasca`, `paita`, `pisco`, `pucallpa`, `puerto_maldonado`, `quillabamba`, `rioja`, `san_pedro_de_lloc`, `san_ramon`, `satipo`, `sicuani`, `sullana`, `talara`, `tarapoto`, `tarma`, `tocache`, `trujillo`, `yurimaguas`

Notas:

- para el listado completo y exacto, ver `bases/maestra/tabla_lenguaje_comun_categorias.csv`
- `territorio` siempre debe leerse junto con `nivel_territorial`
- para mapas se usa la variable derivada `territorio_mapa`, donde `lima`, `lima_metropolitana` y `lima_provincia` se colapsan en `lima_total`

### `causas`

Categorías agregadas comparables:

- `pliego_reclamos`
- `otras_causas`

### `calificacion`

Categorías agregadas comparables:

- `procedente`
- `ilegal`

Estas dos categorías agrupan variantes históricas como:

- `CONFORME ART. 73...`, `CONFORME TUO...`, `CONFORMIDAD`, `PROCEDENCIA`, `PROCEDENTE` -> `procedente`
- `CON AUTO DE ILEGALIDAD`, `ILEGALIDAD`, `IMPROCEDENTE - ILEGALIDAD` -> `ilegal`

### `organizacion`

Categorías agregadas comparables:

- `confederacion`
- `delegados_empleados`
- `delegados_obreros`
- `federacion`
- `sindicato_empleados`
- `sindicato_obreros`
- `sindicato_unico`

### `tamano`

Categorías agregadas comparables:

- `20_49`
- `50_99`
- `100_199`
- `200_299`
- `300_mas`
- `no_indica`

Nota:

- desde 2014 la fuente subdivide el tramo alto en `300-499`, `500-799`, `800-999`, `1000+`; para comparabilidad longitudinal todo eso se agrega en `300_mas`
- `no_indica` aparece cuando el anuario no reporta tamaño para algunos casos

### `duracion`

Categorías agregadas comparables:

- `1_dia`
- `2_3_dias`
- `4_7_dias`
- `8_15_dias`
- `16_mas_dias`

Nota:

- desde 2012 la fuente subdivide el tramo largo en `16-21`, `22-35` y `36+`; para comparabilidad longitudinal todo eso se agrega en `16_mas_dias`

## Bases auxiliares

- `diccionario_idioma_comun_1993_2024.csv`: tabla detallada del idioma común por módulo, categoría fina, categoría agregada y regla observada en la base
- `resumen_idioma_comun_modulos.csv`: resumen por módulo con concepto, nota metodológica y categorías homologadas disponibles
- `tabla_lenguaje_comun_categorias.csv`: tabla canónica por módulo y categoría agregada del lenguaje homologado
- `huelgas_legalidad_1996_2024_largo.csv`: legalidad por año en formato largo
- `huelgas_legalidad_1996_2024_resumen_anual.csv`: resumen anual de legalidad
- `verificacion_calificacion_1993_2024_resumen.csv`: verificación de consistencia del módulo de calificación
- `cruce_anio_sector_largo.csv`: cruce observable `año x sector`
- `cruce_anio_territorio_regional_largo.csv`: cruce observable `año x territorio regional`
