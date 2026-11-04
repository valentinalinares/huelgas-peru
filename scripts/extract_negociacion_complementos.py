"""Extrae complementos nacionales de negociación colectiva del Anuario 2025.

Mantiene valores originales y celdas fuente; los guiones se conservan como
valores no numéricos, nunca como ceros. Las discrepancias se exportan.
"""
from pathlib import Path
import re
import pandas as pd
import openpyxl
from extract_negociacion_colectiva_c56 import SOURCE_2025, OUTPUT_DIR


def clean(value):
    return re.sub(r'\s+', ' ', str(value)).strip()


def main():
    book = openpyxl.load_workbook(SOURCE_2025, data_only=True)
    out = OUTPUT_DIR / 'complementos'
    out.mkdir(exist_ok=True)
    checks = []

    def record(sheet, cell, year, sector, category, unit, note=''):
        raw = sheet[cell].value
        numeric = isinstance(raw, (int, float)) and not isinstance(raw, bool)
        if numeric:
            assert raw >= 0 and int(raw) == raw, (sheet.title, cell, raw)
        return dict(anio=year, actividad_economica=sector, categoria=category,
                    valor=int(raw) if numeric else None, valor_original=raw,
                    estado_valor='numerico' if numeric else 'simbolo_fuente_sin_interpretar',
                    unidad=unit, fuente_documento=SOURCE_2025.name,
                    cuadro=sheet.title, celda=cell, nota=note)

    def save(name, rows):
        df = pd.DataFrame(rows)
        if 'valor' in df:
            df['valor'] = df['valor'].astype('Int64')
            assert not df.duplicated(['anio','actividad_economica','categoria']).any()
        df.to_csv(out / (name + '.csv'), index=False, encoding='utf-8-sig')
        print(name, len(df))
        return df

    def check(name, key, observed, expected):
        checks.append(dict(control=name, clave=key, observado=observed,
                           referencia=expected, diferencia=observed-expected,
                           resultado='coincide' if observed == expected else 'revisar_fuente'))

    s = book['C-50']
    stages = []
    names = ['pliegos_presentados', 'convenios_solucionados_registrados',
             'negociacion_directa', 'conciliacion', 'extra_proceso', 'huelga',
             'autoridad_administrativa_trabajo', 'arbitraje']
    for header, rows in [(8,[9,10,11,12,13,14,16,18]),(27,[28,29,30,31,32,33,35,37])]:
        for cell in s[header]:
            if isinstance(cell.value, int) and 1997 <= cell.value <= 2025:
                for row, name in zip(rows, names):
                    stages.append(record(s, s.cell(row,cell.column).coordinate,
                        cell.value,'Total nacional',name,
                        'pliegos' if name=='pliegos_presentados' else 'convenios',
                        'Incluye pliegos anteriores. En 2025 incluye convenios de 2019–2024 vigentes en 2025.'))
    stages = save('etapas_nacional_1997_2025', stages)
    assert len(stages) == 29*8
    for year, group in stages.groupby('anio'):
        vals = group.set_index('categoria').valor
        check('suma_etapas_numericas_C50',year,int(vals[names[2:]].sum()),int(vals[names[1]]))

    c56 = pd.read_csv(OUTPUT_DIR / 'base_negociacion_colectiva_c56_1995_2025.csv')
    for year, group in stages.groupby('anio'):
        val = group.loc[group.categoria==names[1],'valor'].iloc[0]
        total = c56.loc[(c56.anio==year)&(c56.sector_id=='total_nacional'),'convenios_colectivos'].iloc[0]
        check('total_C50_vs_C56',year,int(val),int(total))

    for sheet, label_col, start_col, categories, filename in [
        ('C-60',4,5,['negociacion_directa','conciliacion','extra_proceso','huelga',
                     'arbitraje_acuerdo_partes','arbitraje_unipersonal','arbitraje_potestativo','total'],
                     'etapas_por_actividad_2025'),
        ('C-62',3,4,['federacion','sindicato_empleados','sindicato_obreros','sindicato_unico',
                     'delegados_empleados','delegados_obreros','delegados_empleados_obreros','total'],
                     'organizacion_por_actividad_2025')]:
        s = book[sheet]
        result=[]
        for row in range(12,28):
            label = clean(s.cell(row,label_col).value) if row<27 else 'Total nacional'
            for col,cat in enumerate(categories,start_col):
                result.append(record(s,s.cell(row,col).coordinate,2025,label,cat,'convenios',
                    'Incluye convenios de 2019–2024 vigentes en 2025.'))
            values=[s.cell(row,c).value for c in range(start_col,start_col+8)]
            check('suma_categorias_'+sheet,label,sum(values[:-1]),values[-1])
            key = re.sub(r'[^A-Z0-9]','',label.upper())
            source = c56[(c56.anio==2025) & c56.actividad_original_mtpe.map(
                lambda v: re.sub(r'[^A-Z0-9]','',v.upper())==key)]
            if row==27:
                source=c56[(c56.anio==2025)&(c56.sector_id=='total_nacional')]
            if len(source)==0 and label.startswith('ACTIVID.'):
                source=c56[(c56.anio==2025)&(c56.sector_id=='actividades_inmobiliarias_empresariales_alquiler')]
            assert len(source)==1, label
            check(sheet+'_vs_C56',label,values[-1],int(source.convenios_colectivos.iloc[0]))
        df=save(filename,result)
        assert len(df)==128
        for cat in categories:
            part=df[df.categoria==cat]
            check('suma_actividades_'+sheet,cat,int(part[part.actividad_economica!='Total nacional'].valor.sum()),
                  int(part[part.actividad_economica=='Total nacional'].valor.iloc[0]))

    s=book['C-68']
    awards=[]
    for header,first,total in [(8,9,25),(28,29,45)]:
        for cell in s[header]:
            if isinstance(cell.value,int) and 1993<=cell.value<=2025:
                for row in list(range(first,first+15))+[total]:
                    label='Total nacional' if row==total else clean(s.cell(row,2).value)
                    awards.append(record(s,s.cell(row,cell.column).coordinate,cell.value,label,
                        'laudos_registrados','laudos',
                        'C-68 no explicita exclusión territorial; C-70 excluye Callao desde 2011. Revisar comparabilidad.'))
    awards=save('laudos_por_actividad_1993_2025',awards)
    assert len(awards)==33*16
    for year,g in awards.groupby('anio'):
        check('suma_actividades_C68',year,int(g[g.actividad_economica!='Total nacional'].valor.sum()),
              int(g[g.actividad_economica=='Total nacional'].valor.iloc[0]))

    s=book['C-70']
    appointments=[]
    for row in range(9,42):
        year=int(re.search(r'\d{4}',str(s.cell(row,2).value)).group())
        for col,category in zip([3,5,7,9,11,13,15],
            ['acuerdo_partes','resolucion_directoral','resolucion_ministerial',
             'arbitraje_unipersonal','potestativo','no_indica','total']):
            appointments.append(record(s,s.cell(row,col).coordinate,year,'Total nacional',category,
                'laudos','Excluye DRTPE Callao.' if year>=2011 else ''))
        check('suma_designacion_C70',year,sum(s.cell(row,c).value for c in [3,5,7,9,11,13]),s.cell(row,15).value)
        val=int(awards[(awards.anio==year)&(awards.actividad_economica=='Total nacional')].valor.iloc[0])
        check('total_C70_vs_C68',year,s.cell(row,15).value,val)
        if year>=1997:
            other=int(stages[(stages.anio==year)&(stages.categoria=='arbitraje')].valor.iloc[0])
            check('arbitraje_C50_vs_C68',year,other,val)
    save('laudos_designacion_1993_2025',appointments)
    save('controles_complementos',checks)

    inventory=[]
    for s in book:
        if not s.title.startswith('C-'): continue
        cells=[clean(c.value) for row in s.iter_rows(max_row=8) for c in row if isinstance(c.value,str)]
        titles=[v for v in cells if len(v)>55]
        inventory.append(dict(cuadro=s.title,titulo=' '.join(titles),
            ambito='Lima Metropolitana' if any('LIMA' in v for v in cells) else 'Perú',
            extraido=s.title in ['C-50','C-56','C-60','C-62','C-68','C-70'],fuente=SOURCE_2025.name))
    save('inventario_capitulo2_2025',inventory)
    print('Discrepancias:',[c for c in checks if c['resultado']!='coincide'])
    book.close()


if __name__=='__main__':
    main()
