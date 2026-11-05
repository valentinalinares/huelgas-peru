"""Auditoría independiente de valores fuente y agregaciones de Planilla."""
from pathlib import Path
import math
import hashlib
import pandas as pd
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

root=Path(__file__).resolve().parents[1]
out=root/'bases'/'planilla_electronica'
m=pd.read_csv(out/'base_mensual.csv')
a=pd.read_csv(out/'base_anual.csv')
wide=pd.read_csv(out/'resumen_anual.csv')
inventory=pd.read_csv(out/'inventario_fuentes.csv')
records=pd.concat([m,a[a.metodo_anual=='promedio_publicado_MTPE']],ignore_index=True)
checked=0
for file,group in records.groupby('archivo'):
    path=root/Path(*file.replace('\\','/').split('/'))  # rutas guardadas en Windows o Linux
    assert hashlib.sha256(path.read_bytes()).hexdigest()==inventory[inventory.archivo==file].sha256.iloc[0]
    excel=pd.ExcelFile(path)
    for sheet,rows in group.groupby('hoja'):
        original=excel.parse(sheet,header=None,nrows=70)
        for row in rows.itertuples():
            col,r=coordinate_from_string(row.celda)
            expected=original.iat[r-1,column_index_from_string(col)-1]
            assert math.isclose(row.valor,float(expected),rel_tol=1e-12,abs_tol=1e-8),(file,sheet,row.celda)
            checked+=1
    excel.close()
for row in a[a.metodo_anual=='promedio_simple_12_meses'].itertuples():
    values=m[(m.anio==row.anio)&(m.sector==row.sector)&(m.indicador==row.indicador)]
    assert set(values.mes)==set(range(1,13)) and len(values)==12
    expected=math.fsum(values.valor)/12
    assert math.isclose(row.valor,expected,rel_tol=1e-12,abs_tol=1e-8)
for row in wide.itertuples():
    assert math.isclose(row.tasa_sindicalizacion_pct,100*row.sindicalizados/row.empleo,rel_tol=1e-12)
assert len(m)==2808 and len(a)==258
assert not m.duplicated(['anio','mes','sector','indicador']).any()
assert not a.duplicated(['anio','sector','indicador']).any()
print(f'{checked} celdas originales verificadas; 234 promedios recalculados; 54 tasas verificadas.')
