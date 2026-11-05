"""Gráficos descriptivos reproducibles de C-56 y C-60."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]/'bases'/'negociacion_colectiva'
out=root/'graficos'
out.mkdir(exist_ok=True)
d=pd.read_csv(root/'serie_mineria_manufactura_total_1995_2025.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,5.5),sharex=True)
for ax,col,title,color in [(axes[0],'mineria_minas_y_canteras','Minería y manufactura','#28786B'),
                          (axes[1],'total_nacional','Total nacional','#485566')]:
    ax.plot(d.anio,d[col],label='Minas y canteras' if ax==axes[0] else 'Total nacional',color=color,lw=2)
    if ax==axes[0]:
        ax.plot(d.anio,d.manufactura,label='Manufactura',color='#B87832',lw=2)
    ax.set_title(title)
    ax.axvspan(2012.5,2019.5,color='#9A9A9A',alpha=.08,lw=0)
    ax.axvline(2019.5,color='#9A9A9A',linestyle=':',lw=1)
    ax.set_ylabel('Convenios solucionados–registrados')
    ax.set_xlabel('Año')
    ax.grid(axis='y',alpha=.18)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
fig.suptitle('Negociación colectiva en Perú, 1995–2025',fontsize=16)
fig.text(.06,.03,'Fuente: MTPE, Anuario 2025, C-56. Franja gris (2013–2019): no incluye convenios supraregionales (D.S. 017-2012-TR), publicados aparte.\nLínea punteada: desde 2020 cada año incluye convenios solucionados en años anteriores que siguen vigentes (nota de cada anuario).\nMinería corresponde a explotación de minas y canteras. Los paneles usan escalas verticales distintas.',fontsize=9)
fig.tight_layout(rect=(0,.16,1,.94))
fig.savefig(out/'convenios_1995_2025.png',dpi=180)
plt.close(fig)

d=pd.read_csv(root/'complementos'/'etapas_por_actividad_2025.csv')
labels=['EXPLOTACIÓN DE MINAS Y CANTERAS','INDUSTRIAS MANUFACTURERAS','Total nacional']
cats=['negociacion_directa','conciliacion','extra_proceso','huelga']
names=['Negociación directa','Conciliación','Extra proceso','Huelga']
colors=['#28786B','#B87832','#788CA8','#8A5869']
fig,ax=plt.subplots(figsize=(10,5))
bottom=[0,0,0]
for cat,name,color in zip(cats,names,colors):
    values=[int(d[(d.actividad_economica==label)&(d.categoria==cat)].valor.iloc[0]) for label in labels]
    ax.barh(['Minas y canteras','Manufactura','Total nacional'],values,left=bottom,label=name,color=color)
    bottom=[a+b for a,b in zip(bottom,values)]
for i,total in enumerate(bottom): ax.text(total+4,i,str(total),va='center')
ax.set_xlim(0,450)
ax.set_xlabel('Número de convenios')
ax.set_title('Etapas de solución de los convenios, 2025')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,frameon=False)
fig.text(.08,.03,'Fuente: MTPE, Anuario 2025, C-60. Incluye convenios anteriores vigentes en 2025.\nEl total nacional incluye minería, manufactura y las demás actividades. Arbitraje: cero en los tres grupos.',fontsize=9)
fig.tight_layout(rect=(0,.19,1,1))
fig.savefig(out/'etapas_solucion_2025.png',dpi=180)
plt.close(fig)

# Evolución de las principales etapas de solución como porcentaje del total.
hist=pd.read_csv(root/'complementos'/'etapas_por_actividad_1995_2025.csv')
hist['valor_num']=pd.to_numeric(hist.valor,errors='coerce')
groups=[('minas_canteras','Minas y canteras'),
        ('industrias_manufactureras','Manufactura'),
        ('total_nacional','Total nacional')]
stage_cats=[('negociacion_directa','Negociación directa','#28786B'),
            ('conciliacion','Conciliación','#B87832'),
            ('extra_proceso','Extra proceso','#788CA8')]
fig,axes=plt.subplots(1,3,figsize=(14,4.8),sharex=True,sharey=True)
for ax,(sector,title) in zip(axes,groups):
    part=hist[hist.sector_id==sector].pivot(index='anio',columns='categoria',values='valor_num')
    total=part['total']
    for category,label,color in stage_cats:
        share=100*part[category]/total
        ax.plot(share.index,share,label=label,color=color,lw=2)
    ax.set_title(title)
    ax.set_xlabel('Año')
    ax.set_ylim(0,105)
    ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('Porcentaje de convenios del sector')
axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.2),ncol=3,frameon=False)
fig.suptitle('Principales etapas de solución, 1995–2025',fontsize=16)
fig.text(.055,.015,'Fuente: anuarios MTPE, cuadros nacionales por actividad. Los guiones de la fuente se mantienen como faltantes; no se convierten en cero.\nEl total nacional incluye todas las actividades. Desde 2020 cada año incluye convenios de años anteriores que siguen vigentes.',fontsize=9)
fig.tight_layout(rect=(0,.14,1,.93))
fig.savefig(out/'etapas_solucion_1995_2025.png',dpi=180)
plt.close(fig)

# Evolución de los tres tipos principales de organización sindical.
org=pd.read_csv(root/'complementos'/'organizacion_por_actividad_1995_2025.csv')
org['valor_num']=pd.to_numeric(org.valor,errors='coerce')
org_cats=[('sindicato_empleados','Sindicato de empleados','#788CA8'),
          ('sindicato_obreros','Sindicato de obreros','#B87832'),
          ('sindicato_unico','Sindicato único','#28786B')]
fig,axes=plt.subplots(1,3,figsize=(14,4.8),sharex=True,sharey=True)
for ax,(sector,title) in zip(axes,groups):
    part=org[org.sector_id==sector].pivot(index='anio',columns='categoria',values='valor_num')
    total=part['total']
    for category,label,color in org_cats:
        share=100*part[category]/total
        ax.plot(share.index,share,label=label,color=color,lw=2)
    ax.set_title(title)
    ax.set_xlabel('Año')
    ax.set_ylim(0,100)
    ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('Porcentaje de convenios del sector')
axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.2),ncol=3,frameon=False)
fig.suptitle('Convenios por tipo de organización sindical, 1995–2025',fontsize=16)
fig.text(.055,.015,'Fuente: anuarios MTPE, cuadros nacionales por actividad. Se muestran los tres tipos principales; federaciones, comités y delegados permanecen en la base.\nLas categorías clasifican convenios, no personas sindicalizadas ni el número de sindicatos existentes.',fontsize=9)
fig.tight_layout(rect=(0,.14,1,.93))
fig.savefig(out/'organizacion_sindical_1995_2025.png',dpi=180)
plt.close(fig)
