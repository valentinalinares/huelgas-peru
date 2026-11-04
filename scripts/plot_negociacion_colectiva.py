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
    ax.set_ylabel('Convenios solucionados–registrados')
    ax.set_xlabel('Año')
    ax.grid(axis='y',alpha=.18)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
fig.suptitle('Negociación colectiva en Perú, 1995–2025',fontsize=16)
fig.text(.06,.04,'Fuente: MTPE, Anuario 2025, C-56. En 2025 se incluyen convenios de 2019–2024 vigentes en 2025.\nMinería corresponde a explotación de minas y canteras. Los paneles usan escalas verticales distintas.',fontsize=9)
fig.tight_layout(rect=(0,.13,1,.94))
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
