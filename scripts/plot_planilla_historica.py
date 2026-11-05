"""Figuras para las series anuales de Planilla Electrónica."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

root=Path(__file__).resolve().parents[1]/'bases'/'planilla_electronica'
out=root/'graficos'
out.mkdir(exist_ok=True)
d=pd.read_csv(root/'resumen_anual.csv')
palette={'mineria':'#28786B','manufactura':'#B87832','total_nacional':'#485566'}
labels={'mineria':'Minas y canteras','manufactura':'Manufactura','total_nacional':'Total nacional privado'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})


def line(ax,indicator,groups,title,unit,scale=1,mark=False,ruptura=False):
    for sector in groups:
        g=d[d.sector==sector].dropna(subset=[indicator])
        ax.plot(g.anio,g[indicator]/scale,label=labels[sector],color=palette[sector],lw=2)
    ax.set_title(title,loc='left',fontweight='bold')
    ax.set_ylabel(unit)
    ax.set_xticks([2008,2012,2016,2020,2025])
    ax.set_ylim(bottom=0)
    ax.grid(axis='y',alpha=.2)
    ax.legend(frameon=False,fontsize=9)
    if mark:
        ax.axvline(2011.5,color='#9A9A9A',linestyle=':',lw=1)
    if ruptura:
        ax.axvline(2012.5,color='#5F5F5F',linestyle='--',lw=1)
        ax.annotate('T-Registro/PLAME',xy=(2012.6,ax.get_ylim()[1]*0.97),fontsize=8,color='#5F5F5F',va='top')


fig,axs=plt.subplots(2,2,figsize=(12,8))
line(axs[0,0],'empleo',['mineria','manufactura'],'Empleo: minería y manufactura','Miles de trabajadores',1000)
line(axs[0,1],'empleo',['total_nacional'],'Empleo: total nacional privado','Millones de trabajadores',1e6)
line(axs[1,0],'tasa_sindicalizacion_pct',list(palette),'Sindicalización','% de trabajadores',mark=True,ruptura=True)
line(axs[1,1],'remuneracion',list(palette),'Remuneración promedio','Soles nominales',mark=True)
fig.suptitle('Planilla Electrónica de Perú, 2008–2025',fontsize=16)
fig.text(.07,.025,'Fuente: MTPE, anuarios 2008–2025. Promedios simples de 12 meses; sindicalización y remuneración 2008–2011: promedios publicados.\nLínea punteada: cambio de origen del promedio en 2012. Línea discontinua: posible ruptura de sindicalización entre 2012 y 2013 (paso de PDT 0601 a T-Registro/PLAME).\nTasa = promedio de sindicalizados / promedio de empleo × 100.\nMinería corresponde a minas y canteras; total nacional limitado al sector privado registrado. Remuneraciones sin ajuste por inflación.',fontsize=9)
fig.tight_layout(rect=(0,.12,1,.95))
fig.savefig(out/'planilla_2008_2025.png',dpi=180)
plt.close(fig)

fig,axs=plt.subplots(2,2,figsize=(12,8))
for row,indicator in enumerate(['intermediacion','tercerizacion']):
    title='Intermediación laboral' if row==0 else 'Tercerización'
    line(axs[row,0],indicator,['mineria','manufactura'],title+': sectores','Miles de trabajadores',1000)
    line(axs[row,1],indicator,['total_nacional'],title+': total nacional privado','Miles de trabajadores',1000)
fig.suptitle('Trabajadores en empresas de intermediación y tercerización',fontsize=15)
fig.text(.07,.03,'Fuente: MTPE, anuarios de Planilla Electrónica. Promedio simple de 12 meses. Intermediación: 2009–2025; tercerización: 2011–2025.\nClasificación por actividad de la empresa registrada: no identifica necesariamente el sector de la empresa usuaria.\nLos paneles tienen distintas escalas verticales. No se suman estas categorías al empleo ni se supone que sean mutuamente excluyentes.',fontsize=9)
fig.tight_layout(rect=(0,.12,1,.95))
fig.savefig(out/'intermediacion_tercerizacion.png',dpi=180)
plt.close(fig)
