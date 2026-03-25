# Nota metodologica: sector y territorio

No se construyo un cruce directo `sector x territorio` dentro de la base maestra principal porque esa combinacion no se observa en los modulos simples anuales (`actividad` y `territorio`) sino en el cuadro cruzado `actividad x territorio` de la base complementaria.

La base maestra actual permite:

- `anio x sector`
- `anio x territorio` (usando solo nivel `regional` para evitar duplicacion)
- `legalidad x anio`

No permite observar directamente:

- `legalidad x sector`
- `legalidad x territorio`
- `sector x territorio` para toda la serie

Para esos cruces se requiere una extraccion adicional del cuadro cruzado `actividad x territorio`, que no forma parte del pipeline principal usado para homogenizar `1993-2024`.
