# Nota metodologica: sector privado y presencia del sector publico

Varios anuarios de huelgas del MTPE aluden en su titulo a `sector privado` o sugieren una cobertura privada. Sin embargo, en los cuadros de actividad economica aparecen de forma explicita categorias como:

- `administracion publica y defensa`
- `ensenanza`
- `servicios sociales y de salud`

## Que se hizo en la homologacion

- no se eliminaron esas filas
- no se recodificaron como si fueran `sector privado`
- no se imputo una separacion artificial entre conflicto publico y privado
- se conservaron tal como aparecen en la fuente y se homologaron a categorias observables del idioma comun, por ejemplo `administracion publica y defensa -> adm_publica`

## Interpretacion

El problema no es del pipeline sino de la propia fuente oficial: la titulacion historica de algunos anuarios no coincide plenamente con el contenido de los cuadros.

Por eso la base maestra debe leerse asi:

- `adm_publica`, `ensenanza` y `salud_social` son categorias validas observadas en la fuente
- su presencia documenta que el registro oficial incluye conflictividad fuera de un sector privado estricto
- esta inconsistencia conceptual debe reportarse en cualquier uso analitico o publicacion
