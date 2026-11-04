# Registros sindicales del MTPE, 1993–2025

Este bloque separa tres conceptos que no deben confundirse:

1. **Flujos administrativos anuales**: registros, cancelaciones, cambios de junta y reformas/modificaciones.
2. **Nuevos sindicatos privados por actividad económica**: registros del año, con detalle mensual desde 2002.
3. **Organizaciones sindicales vigentes**: stock disponible solamente para 2002 en los anuarios revisados.

## Archivos

- `registros_privados_anual.csv`: flujos del sector privado, 1993–2025.
- `registros_publicos_anual.csv`: flujos del sector público (ROSSP), 2004–2025.
- `sindicatos_privados_actividad_anual.csv`: detalle mensual por actividad, 2002–2025.
- `organizaciones_vigentes_2002.csv`: stock nacional de 2002.
- `inventario_fuentes.csv`, `cobertura.csv` y `controles.csv`: trazabilidad y verificaciones.
- `registros_y_cancelaciones_1993_2025.png` y `sindicatos_por_actividad_2002_2025.png`: gráficos descriptivos.

## Cobertura y comparabilidad

- La serie privada retrospectiva del cuadro 116 de 2025 cubre 1993–2025.
- La serie pública retrospectiva del cuadro 122 cubre 2004–2025.
- Los cuadros anuales por actividad permiten comparar explotación de minas y canteras, manufactura y total nacional desde 2002.
- El cuadro de actividad publicado en el Anuario 2008 suma 203 sindicatos, mientras el cuadro retrospectivo de 2025 informa 201 para 2008. Se conservan ambos valores y el control marca una diferencia de 2; no se corrige silenciosamente.
- `explotación de minas y canteras` no equivale exactamente a minería metálica y puede excluir contratistas clasificados en otras actividades.
- Los registros son actos administrativos; no miden por sí solos el número de sindicatos activos. El stock de 2002 se mantiene en una base separada.

## Reproducción

```bash
python scripts/extract_registros_sindicales.py
python scripts/validate_registros_sindicales.py
python scripts/plot_registros_sindicales.py
```

Cada observación conserva archivo, hoja, celda/rango y huella SHA-256 del original.
