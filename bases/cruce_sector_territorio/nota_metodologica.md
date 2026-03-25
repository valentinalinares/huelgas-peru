# Nota metodologica: cruce sector x territorio

Se extrajo una base complementaria del cuadro `actividad x territorio` para los años donde ese cuadro existe y fue legible con un parser reproducible.

- anos disponibles en esta fase: 2001-2024
- la base resultante no reemplaza la base maestra principal; la complementa
- en `2001-2013` varias zonas quedan sin `territorio_padre` inferido automaticamente para evitar asignaciones territoriales equivocadas en los layouts antiguos
- en `2014-2024` se aprovecha mejor la jerarquia region/zona del cuadro

## Años sin cuadro cruzado disponible en esta fase

- `1993`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1994`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1995`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1996`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1997`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1998`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `1999`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)
- `2000`: no_disponible (No existe cuadro cruzado utilizable en el pipeline actual.)

## Validacion

Para cada territorio se verifico, por metrica, que la suma de sectores coincida con el total absoluto del mismo cuadro.
La validacion se guarda en `validacion_sector_territorio_2001_2024.csv`.