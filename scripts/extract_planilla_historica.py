"""Series de Planilla Electrónica 2008–2025 con celdas fuente y controles.

Requiere pandas, openpyxl y xlrd. Lee originales sin modificarlos.
Las fuentes anuales tempranas se distinguen del promedio calculado de 12 meses.
"""
from pathlib import Path
import re
import unicodedata
import hashlib
import pandas as pd
from openpyxl.utils import get_column_letter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'bases'/'planilla_electronica'
MONTHS='ENERO FEBRERO MARZO ABRIL MAYO JUNIO JULIO AGOSTO SETIEMBRE OCTUBRE NOVIEMBRE DICIEMBRE'.split()
INDICATORS=['empleo','sindicalizados','intermediacion','tercerizacion','remuneracion']


RUPTURAS_SINDICALIZACION={
    2012:('Año de transición: la fuente declara PDT 0601 y T-Registro/PLAME. Los sindicalizados suben entre '
          'octubre de 2012 y enero de 2013 sin un salto equivalente del empleo.'),
    2013:('Primer año solo con T-Registro/PLAME. El promedio anual de sindicalizados sube 56% en el total, '
          '37% en minería y 34% en manufactura respecto de 2012. Comparar con años previos con cautela.'),
}
RUPTURA_CORTA={2012:'transicion_PDT0601_a_T-Registro_PLAME',2013:'primer_anio_T-Registro_PLAME'}


def norm(value):
    return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFD',str(value).upper())
                                   if not unicodedata.combining(c))).strip()


def source(year):
    files=[p for p in (ROOT/'anuarios'/str(year)).rglob('*')
           if p.suffix.lower() in ['.xls','.xlsx'] and 'PLANILL' in p.name.upper()
           and any(v in p.name for v in ['01','03','04']) and 'LIMA' not in p.name.upper()]
    assert len(files)==1,(year,files)
    return files[0]


def config(year):
    # Hoja, modalidad de extracción, columna de valor anual (base cero).
    if year==2008:
        return {'empleo':('47','mensual',None),'sindicalizados':('57','publicado',11),
                'remuneracion':('59','publicado',33)}
    if year<=2011:
        result={'empleo':('16','mensual',None),'sindicalizados':('26','publicado',11),
                'remuneracion':('30' if year==2009 else '30N','publicado',34),
                'intermediacion':('28','mensual',None)}
        if year==2011: result['tercerizacion']=('40','mensual',None)
        return result
    if year==2012: sheets=['C-42','C-47','C-48','C-48','C-49']
    elif year==2013: sheets=['C-52','C-59','C-60','C-60','C-74']
    elif year<=2023: sheets=['C-52' if year==2014 else 'C-9','C-16','C-17','C-17','C-33']
    else: sheets=['c7','c14','c15','c15','c31']
    return {indicator:(sheet,'mensual',None) for indicator,sheet in zip(INDICATORS,sheets)}


def sector(label):
    text=norm(label)
    if 'MINAS Y CANTERAS' in text:return 'mineria'
    if text=='INDUSTRIAS MANUFACTURERAS':return 'manufactura'
    if text.startswith('TOTAL'):return 'total_nacional'
    return None


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    monthly,annual,inventory,checks,early_controls=[],[],[],[],[]
    for year in range(2008,2026):
        path=source(year)
        excel=pd.ExcelFile(path)
        cache={}
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        for indicator,(sheet,mode,value_col) in config(year).items():
            if sheet not in cache:cache[sheet]=excel.parse(sheet,header=None,nrows=70)
            d=cache[sheet]
            header=' '.join(norm(v) for v in d.iloc[:10,:4].values.flatten() if pd.notna(v))
            assert 'LIMA METROPOLITANA' not in header,(year,sheet)
            assert 'PERU' in header or 'NIVEL NACIONAL' in header,(year,sheet)
            assert 'PRIVADO' in header and 'ACTIVIDAD ECONOMICA' in header,(year,sheet)
            # Verifica el año del cuadro, sin inferirlo únicamente del nombre del archivo.
            assert re.search(r'\b'+str(year)+r'\b',header),(year,sheet,header)
            table=next(str(v).strip() for v in d.iloc[:5,:4].values.flatten() if 'CUADRO' in str(v))
            if mode=='mensual':
                options=[]
                for r in range(min(16,len(d))):
                    cols=[(c,MONTHS.index(norm(v))+1) for c,v in enumerate(d.iloc[r]) if norm(v) in MONTHS]
                    if len(cols)==12: options.append((r,cols))
                assert options,(year,sheet,'No hay 12 meses')
                header_row,columns=options[0]
                label_col=columns[0][0]-1
                if year>=2012 and indicator in ['intermediacion','tercerizacion']:
                    offset=0 if indicator=='intermediacion' else 1
                    assert 'INTER' in norm(d.iat[header_row+1,columns[0][0]])
                    assert 'TERC' in norm(d.iat[header_row+1,columns[0][0]+1])
                    columns=[(c+offset,m) for c,m in columns]
                first=header_row+1
            else:
                label_col=0 if year==2008 and indicator=='remuneracion' else 1
                first=9
                columns=[(value_col,0)]
                if indicator=='sindicalizados':assert norm(d.iat[8,value_col])=='SINDICALIZADO'
                else: assert 'TOTAL PROMEDIO MENSUAL' in norm(d.iat[6,value_col])
            totals=[r for r in range(first,len(d)) if norm(d.iat[r,label_col]).startswith('TOTAL')]
            assert totals,(year,sheet)
            end=totals[0]
            selected=[r for r in range(first,end+1) if sector(d.iat[r,label_col])]
            assert len(selected)==3,(year,sheet,selected)
            notes=' | '.join(str(v).strip() for v in d.iloc[end+1:,:min(4,len(d.columns))].values.flatten()
                             if pd.notna(v) and isinstance(v,str))
            inventory.append(dict(anio=year,indicador=indicator,archivo=str(path.relative_to(ROOT)),
                sha256=sha,hoja=sheet,cuadro=table,modalidad=mode,notas_fuente=notes))
            for row in selected:
                group=sector(d.iat[row,label_col])
                for col,month in columns:
                    raw=d.iat[row,col]
                    numeric=pd.notna(raw) and isinstance(raw,(int,float))
                    value=float(raw) if numeric else None
                    assert value is None or value>=0,(year,sheet,row,col)
                    item=dict(anio=year,mes=month,sector=group,indicador=indicator,valor=value,
                        valor_original=raw if pd.notna(raw) else '',
                        estado_valor='numerico' if numeric else 'sin_dato_o_simbolo',
                        unidad='soles_nominales' if indicator=='remuneracion' else 'trabajadores',
                        ambito='Peru_sector_privado',actividad_original=str(d.iat[row,label_col]).strip(),
                        archivo=str(path.relative_to(ROOT)),hoja=sheet,cuadro=table,
                        celda=f'{get_column_letter(col+1)}{row+1}')
                    if mode=='mensual': monthly.append(item)
                    else:
                        item.update(metodo_anual='promedio_publicado_MTPE',meses_disponibles=None,
                            observacion='Promedio publicado; no se reconstruyen meses. Comparabilidad con serie mensual por revisar.')
                        annual.append(item)
                        if indicator=='sindicalizados':
                            early_controls.append(dict(anio=year,sector=group,
                                empleo_promedio_publicado=d.iat[row,12],hoja=sheet,
                                celda=f'M{row+1}'))
            if indicator!='remuneracion':
                for col,month in columns:
                    body=d.iloc[first:end,col]
                    # Excluye filas de encabezados y conserva faltantes en filas de actividad.
                    body=body[[isinstance(d.iat[r,label_col],str) and
                               norm(d.iat[r,label_col]) not in ['', 'ACTIVIDAD ECONOMICA']
                               for r in range(first,end)]]
                    numeric=pd.to_numeric(body,errors='coerce')
                    published=d.iat[end,col]
                    delta=float(numeric.sum()-published)
                    missing=int(numeric.isna().sum())
                    checks.append(dict(control='suma_actividades_vs_total',anio=year,mes=month,
                        indicador=indicator,sector='total_nacional',diferencia=delta,
                        faltantes_componentes=missing,resultado='revisar_diferencia' if abs(delta)>1e-6 else
                        ('coincide_con_faltantes' if missing else 'coincide')))
        excel.close()
        print(year,'extraido',flush=True)
    m=pd.DataFrame(monthly)
    assert not m.duplicated(['anio','mes','sector','indicador']).any()
    for key,g in m.groupby(['anio','sector','indicador']):
        assert len(g)==12
        item=g.sort_values('mes').iloc[0].to_dict()
        item.update(mes=0,valor=g.valor.mean() if g.valor.notna().sum()==12 else None,
                    valor_original='',estado_valor='calculado' if g.valor.notna().sum()==12 else 'incompleto',
                    celda=';'.join(g.sort_values('mes').celda),
                    metodo_anual='promedio_simple_12_meses',meses_disponibles=int(g.valor.notna().sum()),
                    observacion='Media de promedios mensuales, no remuneración anual individual.' if key[2]=='remuneracion'
                    else 'Promedio mensual del año; no personas únicas anuales.')
        annual.append(item)
    a=pd.DataFrame(annual).sort_values(['anio','indicador','sector'])
    assert not a.duplicated(['anio','sector','indicador']).any()
    # Posible ruptura de sindicalización por el cambio de registro (PDT 0601 a T-Registro/PLAME).
    a['posible_ruptura']=[RUPTURAS_SINDICALIZACION.get(r.anio,'') if r.indicador=='sindicalizados' else ''
                          for r in a.itertuples()]
    for rec in early_controls:
        employment=a[(a.anio==rec['anio'])&(a.sector==rec['sector'])&(a.indicador=='empleo')].valor.iloc[0]
        delta=float(rec['empleo_promedio_publicado']-employment)
        checks.append(dict(control='empleo_promedio_cuadro_sindicalizacion_vs_mensual',anio=rec['anio'],mes=0,
            indicador='empleo',sector=rec['sector'],diferencia=delta,faltantes_componentes=0,
            resultado='coincide' if abs(delta)<1e-6 else 'revisar_diferencia'))
    joined=m.pivot(index=['anio','mes','sector'],columns='indicador',values='valor')
    for key,r in joined.dropna(subset=['empleo','sindicalizados']).iterrows():
        checks.append(dict(control='sindicalizados_no_superan_empleo',anio=key[0],mes=key[1],sector=key[2],
            indicador='sindicalizados',diferencia=max(0,r.sindicalizados-r.empleo),faltantes_componentes=0,
            resultado='coincide' if r.sindicalizados<=r.empleo else 'revisar_diferencia'))
    coverage=[]
    for indicator in INDICATORS:
        for year in range(2008,2026):
            g=a[(a.anio==year)&(a.indicador==indicator)]
            coverage.append(dict(anio=year,indicador=indicator,sectores=len(g),
                estado='extraido' if len(g)==3 else 'no_identificado_en_cuadros_revisados',
                metodo=g.metodo_anual.iloc[0] if len(g) else ''))
    wide=a.pivot(index=['anio','sector'],columns='indicador',values='valor').reset_index()
    wide['tasa_sindicalizacion_pct']=100*wide.sindicalizados/wide.empleo
    wide['posible_ruptura_sindicalizacion']=wide.anio.map(lambda y:RUPTURA_CORTA.get(y,''))
    assert wide.tasa_sindicalizacion_pct.between(0,100).all()
    for name,frame in [('base_mensual',m),('base_anual',a),('resumen_anual',wide),
                       ('inventario_fuentes',pd.DataFrame(inventory)),('cobertura',pd.DataFrame(coverage)),
                       ('controles',pd.DataFrame(checks))]:
        frame.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig')
    print('Mensuales',len(m),'Anuales',len(a),'Faltantes mensuales',m.valor.isna().sum())
    print(pd.DataFrame(checks).groupby(['control','resultado']).size().to_string())
    print(wide[wide.anio==2025].to_string(index=False))


if __name__=='__main__':main()
