# Guía del repositorio: Huelgas Perú 1993–2024

Este documento explica qué contiene el repositorio, cómo está organizado, qué decisiones metodológicas se tomaron y por qué. Está pensado para quien necesite presentar, defender o replicar el trabajo, ya sea ante un colega, un revisor o en una publicación académica.

---

## Qué es este repositorio

Este repositorio construye una base longitudinal homologada de huelgas en Perú para el período 1993–2024, a partir de los anuarios estadísticos oficiales del Ministerio de Trabajo y Promoción del Empleo (MTPE).

La fuente oficial es valiosa pero no está pensada para el análisis comparativo. Cada anuario tiene su propio layout, su propia numeración de hojas, sus propias etiquetas de categorías y sus propios criterios de presentación. Comparar 1999 con 2019 directamente no es posible sin un trabajo previo de traducción sistemática. A eso se llama homologación, y es exactamente lo que este pipeline hace.

El resultado es una sola base donde todos los años hablan el mismo idioma, con las mismas categorías, las mismas unidades de análisis y las mismas advertencias metodológicas preservadas.

---

## Estructura del repositorio

```
github/
├── anuarios/          Archivos fuente originales del MTPE, organizados por año
├── bases/
│   ├── maestra/       Base principal + diccionarios + gráficos
│   ├── era1_homologados/          Años 1994–1995
│   ├── era2_homologados_1996_1999/
│   ├── era2_homologados_2000_2003/
│   ├── era2_homologados_2004_2020/
│   ├── era3_homologados/          Años 2021–2024
│   ├── cruce_sector_territorio/   Base complementaria (2001–2024)
│   ├── mapas_folium/  Mapas interactivos exportados (.html)
│   └── reportes/      Tablas de reporte ejecutivo
├── scripts/           Extractores y consolidadores Python
├── notebooks/         Pipeline documentado en Jupyter
├── shapes/            Capas geográficas para mapas
└── docs/              Metodología, variables y limitaciones
```

---

## Las dos bases principales y la complementaria

En línea con las recomendaciones metodológicas del proyecto, el repositorio produce tres productos tabulares diferenciados, en lugar de intentar una megabase que lo haga todo.

### Base 1: `huelgas_modulos_maestra_1993_2024.csv`

Es la base principal. Cada fila representa una combinación de año + módulo + categoría. Por ejemplo:

| anio | modulo | categoria_homologada_agregada | huelgas | trabajadores_comprendidos | horas_hombre_perdidas |
|------|--------|-------------------------------|---------|--------------------------|----------------------|
| 2024 | actividad | adm_publica | 33 | 47,680 | 1,955,040 |
| 2024 | duracion | 1_dia | 26 | … | … |
| 2024 | calificacion | ilegal | 47 | … | … |

Con esta base se puede responder casi todo lo analíticamente importante: en qué sectores se concentra la huelga, si cambian las causas entre años, si sube la improcedencia, si predominan las huelgas cortas, si el impacto se concentra en pocos conflictos grandes. Es el corazón del análisis.

### Base 2: `resumen_anual_1993_2024.csv`

Es la base resumen histórica. Una fila por año, con totales nacionales. Sirve para contextualizar la serie larga, mostrar años pico, visualizar el desacople entre frecuencia e intensidad, y construir la introducción del paper.

### Base complementaria: `sector_territorio_2001_2024.csv`

Es la extracción del cuadro cruzado `actividad × territorio`, que la fuente solo ofrece de forma homogénea a partir de 2001. No reemplaza a la base maestra sino que amplía los cruces observables: permite ver, por ejemplo, en qué región se concentra la conflictividad minera en cada año.

Esta base tiene su propia validación (`validacion_sector_territorio_2001_2024.csv`) y varios años están marcados como `ok`, `ok_con_salvedad` o `revisar`. Debe usarse con esa advertencia.

**Importante:** que la base complementaria empiece en 2001 no significa que la base maestra empiece ahí. La base maestra cubre 1993–2024. Lo que empieza en 2001 es solo el cruce específico `actividad × territorio`.

---

## Cobertura real por producto

No todos los productos del repositorio cubren exactamente el mismo rango temporal. Esto es intencional y está documentado, no es una inconsistencia:

| Producto | Cobertura |
|----------|-----------|
| Base maestra (módulos simples) | 1993–2024 con salvedades en 1993–1995 |
| Módulos completos comparables | 1996–2024 |
| Mapas territoriales | 1999–2024 |
| Cruce complementario sector × territorio | 2001–2024 |

El año 1993 está excluido del pipeline tabular porque los anuarios de ese año solo existen en formato `.DOC` y no contienen una tabla estructurada. Los años 1994 y 1995 son parciales: tienen datos de actividad, causas, organización y territorio, pero no existe en la fuente el módulo de calificación, tamaño ni duración.

---

## Las eras de procesamiento

Los anuarios del MTPE no cambiaron de golpe: cambiaron gradualmente. Para manejar esa heterogeneidad de forma ordenada, el pipeline divide la serie en cuatro bloques o "eras", cada uno con su extractor específico.

**Era 1 (1994–1995):** años parciales con módulos limitados.

**Era 2 vieja (1996–2003):** layouts más variables, requieren parsers específicos por bloque o incluso por año.

**Era 2 estable (2004–2020):** estructura muy consistente. Es el bloque donde la comparación es más directa y las reglas de homologación más claras.

**Era 3 (2021–2024):** mismos módulos que la era estable, pero cambia la numeración de hojas dentro del anuario. Se procesan con extractores separados para no contaminar la lógica de la era anterior.

Esta división no es arbitraria: refleja cuándo cambia materialmente la estructura del anuario, no cuándo cambia el gobierno o la política laboral.

---

## Qué es la homologación y qué garantiza

La homologación es la traducción sistemática de categorías originales de cada anuario a un lenguaje común que permite comparar todos los años. No implica inventar datos ni corregir la fuente oficial. Implica asignar a cada categoría original una categoría equivalente en el idioma común, con una regla documentada.

La base conserva siempre la categoría original (`categoria_original`) junto con la traducción fina (`categoria_homologada_fina`) y la traducción comparable longitudinalmente (`categoria_homologada_agregada`). Quien quiera revisar cualquier decisión puede trazarla hasta la fuente.

Ejemplos de reglas aplicadas en calificación:

| Categoría original (varía por año) | Categoría homologada |
|-------------------------------------|----------------------|
| `CONFORME ART. 73…` | `procedente` |
| `CONFORME TUO…` | `procedente` |
| `PROCEDENTE` | `procedente` |
| `CON AUTO DE ILEGALIDAD` | `ilegal` |
| `IMPROCEDENTE - ILEGALIDAD` | `ilegal` |

Ejemplos en duración (la fuente amplía el detalle de tramos en años recientes, pero la versión comparable longitudinalmente los agrega):

| Tramos originales (2012 en adelante) | Categoría homologada comparable |
|--------------------------------------|--------------------------------|
| `16 a 21 días`, `22 a 35 días`, `36 días a más` | `16_mas_dias` |

Ejemplos en tamaño (mismo principio):

| Tramos originales (desde 2014) | Categoría homologada comparable |
|--------------------------------|--------------------------------|
| `300-499`, `500-799`, `800-999`, `1000+` | `300_mas` |

La validación de la homologación no es solo documental: para el módulo de calificación, en todos los años con módulo disponible se verificó que `procedente + ilegal` en huelgas, trabajadores y horas coincide con el total fuente. Los resultados están en `verificacion_calificacion_1993_2024_resumen.csv`.

---

## Advertencia metodológica 1: el arrastre de horas-hombre

Esta es una limitación de la fuente oficial, no del pipeline. En varios anuarios, el propio MTPE aclara en notas al pie que las `horas_hombre_perdidas` no corresponden exclusivamente al período inmediato del cuadro, sino que pueden incluir horas generadas por huelgas provenientes del mes anterior. En el caso del cuadro cruzado de 2024, la nota es todavía más amplia y menciona `año y/o mes anterior`.

Lo que esto significa en concreto: si una huelga comienza el 28 de agosto y sigue hasta el 3 de septiembre, el anuario puede imputar las horas de esa continuación al cuadro de septiembre, aunque la huelga no haya nacido ese mes. El dato de horas es correcto como medición oficial acumulada del período reportado; lo que no puede asumirse es que esas horas correspondan solo a huelgas iniciadas en ese período.

**Lo que se hizo:** no se recalcularon las horas, no se redistribuyeron entre meses ni se corrigió el dato oficial. Se conservó el valor original y se marcó en la variable `flag_hhp_arrastre = 1` cada cuadro donde la fuente levanta esa advertencia.

Los años y módulos afectados son:

- **Causas (hoja C-6 o equivalente):** 2003–2008, 2012, 2015–2018, 2021–2024
- **Territorio (hoja C-5 o equivalente):** 2017
- **Actividad (hoja C-94):** 2024

En la base complementaria `sector × territorio`, el caso más fuerte está en 2024 (hoja C-102), donde la nota habla explícitamente de `año y/o mes anterior`.

Para análisis de totales anuales agregados, este efecto es menor. Para análisis de distribución mensual o comparación de horas por módulo en esos años específicos, la advertencia es relevante y debe reportarse.

---

## Advertencia metodológica 2: la inconsistencia sector público / privado

Varios anuarios del MTPE titulan sus cuadros de actividad económica como estadísticas del "sector privado". Sin embargo, al revisar las categorías observadas dentro de esas mismas tablas, aparecen con consistencia categorías como:

- `ADMINISTRACIÓN PÚBLICA Y DEFENSA`
- `ENSEÑANZA`
- `SERVICIOS SOCIALES Y DE SALUD`

Esta no es una contradicción del pipeline sino una inconsistencia de la fuente oficial. El rótulo general sugiere "sector privado", pero la clasificación interna incluye actividades claramente no privadas o de naturaleza mixta. La inconsistencia conceptual está en la estadística del MTPE, no en el procesamiento.

**Lo que se hizo:** esas categorías no se eliminaron, no se forzaron a "sector privado" y no se imputó una separación artificial entre conflictividad pública y privada. Se conservaron exactamente como aparecen en la fuente y se tradujeron a las categorías del lenguaje común (`adm_publica`, `ensenanza`, `salud_social`).

La presencia de `adm_publica` en la base maestra va de 2000 a 2024, ininterrumpida. Eso no es un artefacto de la homologación: es exactamente lo que la fuente oficial reporta. Cualquier análisis que quiera hacer distinciones entre conflicto público y privado tendrá que partir de esa limitación declarada de la estadística oficial, no resolverla artificialmente.

---

## Variables de la base maestra

| Variable | Descripción |
|----------|-------------|
| `anio` | Año del anuario |
| `modulo` | Dimensión temática del cuadro (actividad, territorio, causas, calificacion, organizacion, tamano, duracion) |
| `hoja_excel` | Hoja original del workbook fuente |
| `categoria_original` | Texto exacto observado en la fuente, sin modificar |
| `categoria_homologada_fina` | Traducción conservando el mayor detalle posible |
| `categoria_homologada_agregada` | Traducción comparable longitudinalmente |
| `regla_homologacion` | Explicación breve de la traducción aplicada |
| `nivel_territorial` | `regional` o `zona`, solo para el módulo territorio |
| `territorio_padre` | Región madre de una zona, solo para territorio |
| `huelgas` | Número absoluto de huelgas |
| `trabajadores_comprendidos` | Número absoluto de trabajadores |
| `horas_hombre_perdidas` | Número absoluto de horas-hombre |
| `pct_huelgas` / `pct_trabajadores` / `pct_horas` | Porcentajes dentro del cuadro fuente |
| `flag_hhp_arrastre` | Marca años y módulos donde la fuente advierte arrastre de horas del mes anterior |
| `flag_faltante_fuente` | Marca faltantes declarados por la fuente |
| `nota_fuente` | Concatenación de notas metodológicas del cuadro original |
| `tipo_anio` | `excluido_sin_excel_fuente`, `parcial` o `completo` |

---

## Lo que la base maestra no permite hacer (y por qué)

Hay cruces analíticos que suenan razonables pero que no existen como cuadros observados en la fuente oficial. No son limitaciones del pipeline, son limitaciones de la estadística del MTPE:

- No existe cruce `legalidad × sector`
- No existe cruce `legalidad × territorio`
- No existe cruce `legalidad × organización`

Estos cruces no pueden construirse sin asumir independencia estadística o hacer imputaciones que la fuente no respalda. No se hicieron.

El cruce `sector × territorio` tampoco forma parte de la base maestra principal, porque no existe de forma homogénea para toda la serie. Sí existe como base complementaria para 2001–2024, con su propia validación. Esa base debe usarse con la advertencia de que algunos años están marcados como `revisar`.

---

## Sobre la variable territorio

El módulo territorio es el más complejo y el que más exige precaución analítica.

La fuente mezcla en una misma tabla dos niveles jerárquicos distintos: el nivel regional (Junín, Arequipa, Lima…) y el nivel zona (La Oroya, Pisco, Huacho…). En la base maestra se distinguen con la variable `nivel_territorial`, para no sumarlos como si fueran equivalentes.

Además, Lima cambia de etiqueta a lo largo de la serie:

- 1994–1999: aparece como `lima`
- 2000–2010: aparece como `lima_provincia`
- 2011–2024: aparece como `lima_metropolitana` (y en algunos años también `lima_provincia` por separado)

Estas etiquetas no son tres territorios distintos: son la evolución de cómo la fuente nombra a la misma región a lo largo del tiempo. No deben compararse directamente sin una decisión analítica explícita. Para los mapas interactivos se adoptó una solución cartográfica conservadora: `lima`, `lima_metropolitana` y `lima_provincia` se colapsan en `lima_total`, exclusivamente para fines de visualización. Eso no afecta a la base maestra, donde las etiquetas originales se conservan.

Los mapas territoriales comparables empiezan en 1999, no porque la base maestra empiece ahí, sino porque 1996–1998 todavía usan divisiones regionales históricas (CTAR, macrorregiones) que no tienen equivalencia directa con la capa geográfica contemporánea.

---

## Los mapas interactivos

Los cuatro mapas en `bases/mapas_folium/` son archivos `.html` que se pueden compartir y abrir en cualquier navegador. Cada uno muestra la evolución territorial de una variable a lo largo del tiempo:

1. `01_huelgas_territorio_tiempo.html`: número de huelgas por región
2. `02_trabajadores_territorio_tiempo.html`: trabajadores comprendidos por región
3. `03_horas_hombre_territorio_tiempo.html`: horas-hombre perdidas por región
4. `04_mineria_territorio_tiempo.html`: conflictividad minera por región

**Requisito técnico:** los mapas cargan librerías desde CDN (Leaflet, Folium). Funcionan bien con acceso a internet. Sin conexión, pueden no renderizar correctamente.

---

## Scripts y notebooks

El pipeline está documentado en dos niveles: los scripts Python en `scripts/` son los ejecutores, y los notebooks en `notebooks/` son la versión narrada y revisable del mismo proceso.

| Notebook | Contenido |
|----------|-----------|
| `01_procesamiento_homologacion.ipynb` | Extracción y homologación de todas las eras |
| `02_analisis_base_maestra.ipynb` | Análisis descriptivo de la base maestra |
| `03_mapas_interactivos.ipynb` | Construcción y exportación de mapas Folium |
| `04_cruce_sector_territorio.ipynb` | Extracción y validación de la base complementaria |
| `05_reporte_ejecutivo.ipynb` | Tablas de reporte ejecutivo por región y sector dominante |

Para reproducir el pipeline completo desde cero:

```bash
pip install -r requirements.txt
python scripts/run_publication_pipeline.py
```

Si además se quiere poblar la carpeta `anuarios/` automáticamente desde el portal oficial del MTPE:

```bash
python scripts/download_anuarios.py
```

---

## Documentación de referencia

Todos los archivos de documentación están en `docs/`:

- `metodologia_homologacion.md`: lógica general del pipeline, eras y reglas centrales
- `diccionario_variables.md`: descripción de todas las variables con ejemplos
- `limitaciones_fuente.md`: limitaciones declaradas de la estadística oficial
- `nota_horas_hombre_arrastre.md`: detalle técnico de la advertencia de arrastre por año y módulo
- `checklist_publicacion.md`: lista de verificación antes de publicar o citar la base

Y en `bases/maestra/`:

- `nota_sector_publico_privado.md`: explicación de la inconsistencia conceptual de la fuente respecto al sector privado
- `nota_sector_territorio.md`: consideraciones sobre el cruce sector × territorio
- `tabla_lenguaje_comun_categorias.csv`: tabla canónica con todas las categorías del idioma homologado, su rango temporal y notas metodológicas
- `diccionario_idioma_comun_1993_2024.csv`: detalle de cada traducción aplicada, con la regla observada en la base

---

## Lo que este repositorio permite hacer

Con la base maestra y el resumen anual se puede describir y analizar:

- la evolución de la frecuencia, el tamaño y la intensidad de la huelga a lo largo de tres décadas
- el desacople entre número de huelgas y volumen de trabajadores o horas (pocas huelgas grandes concentran el impacto)
- el desplazamiento sectorial del epicentro del conflicto, desde la minería hacia la administración pública
- la evolución de la calificación legal: qué proporción de huelgas son declaradas ilegales, y si eso cambia con el tiempo
- la distribución territorial del conflicto y el peso histórico de Lima Metropolitana
- la dualidad entre muchas huelgas cortas y pocas huelgas muy largas o muy grandes que concentran las horas perdidas
- si el conflicto no clásico (otras causas, fuera del pliego) aumenta o se alterna históricamente

Con la base complementaria `sector × territorio` se puede además observar en qué regiones específicas se concentra la conflictividad de cada sector económico.

Lo que no se puede hacer con esta base sin imputaciones adicionales: cruzar legalidad con sector, legalidad con territorio, o sector con duración. Esos cruces no existen en la fuente oficial.
