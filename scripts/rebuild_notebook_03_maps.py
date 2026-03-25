from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "03_mapas_interactivos.ipynb"


def md(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata.language_info = {"name": "python"}

nb.cells = [
    md(
        """# 03. Mapas interactivos

Este cuaderno genera cuatro mapas `folium` para seguir la evolución territorial de las huelgas:

- `huelgas` por territorio y año
- `trabajadores_comprendidos` por territorio y año
- `horas_hombre_perdidas` por territorio y año
- `huelgas de minería` por territorio y año

Decisiones metodológicas:

- para mapas se usa `territorio_mapa`
- `lima`, `lima_metropolitana` y `lima_provincia` se colapsan en `lima_total`
- los mapas generales usan `1999-2024`
- el mapa de minería usa `2001-2024`
- solo se usan territorios de nivel `regional` en el mapa de minería

Por qué no se mapea desde `1993`:

- `1993` no tiene Excel usable
- `1994-1995` son años parciales
- `1996-1998` todavía usan regiones históricas no equivalentes 1 a 1 con la geografía contemporánea
- por eso el período cartográficamente comparable arranca en `1999`

Aquí se usa una lógica de capas anuales reales, con selector de año y botón `play`, para evitar los problemas del control temporal anterior.
"""
    ),
    code(
        """from pathlib import Path
import json

import pandas as pd
import geopandas as gpd
import branca.colormap as bcm
import folium
from branca.element import Element, MacroElement, Template
from IPython.display import display, Markdown

ROOT = Path.cwd().resolve()
if (ROOT / 'bases').exists() and (ROOT / 'notebooks').exists():
    project_root = ROOT
else:
    project_root = ROOT.parent

BASE_MAESTRA = project_root / 'bases' / 'maestra'
BASE_CRUCE = project_root / 'bases' / 'cruce_sector_territorio'
SHAPES = project_root / 'shapes'
OUTPUTS = project_root / 'bases' / 'mapas_folium'
OUTPUTS.mkdir(parents=True, exist_ok=True)

cobertura = pd.read_csv(BASE_MAESTRA / 'cobertura_modulos_1993_2024.csv')
territorio_raw = pd.read_csv(BASE_MAESTRA / 'cruce_anio_territorio_regional_largo.csv')
sector_territorio = pd.read_csv(BASE_CRUCE / 'sector_territorio_2001_2024.csv')
equiv = pd.read_csv(SHAPES / 'equivalencias_territorio_mapa.csv')
geo = gpd.read_file(SHAPES / 'peru_territorios_huelga_lima_total.geojson')

geo_map = geo.copy()
geo_map['geometry'] = geo_map.geometry.simplify(0.03, preserve_topology=True)

resumen_anual = (
    cobertura.assign(ok=cobertura['modulo_con_datos'].eq(1))
    .groupby(['anio', 'tipo_anio'], as_index=False)
    .agg(modulos_con_datos=('ok', 'sum'), modulos_total=('modulo', 'size'))
)
resumen_anual['anio_completo'] = resumen_anual['modulos_con_datos'].eq(resumen_anual['modulos_total'])

anios_completos = sorted(resumen_anual.loc[resumen_anual['anio_completo'], 'anio'].tolist())
anios_mapa_general = [anio for anio in anios_completos if anio >= 1999]
anios_mapa_mineria = [anio for anio in anios_completos if anio >= 2001]

resumen_anual.tail(12)
"""
    ),
    md(
        """## Universo temporal de los mapas

- `1993` queda fuera porque no tiene Excel fuente
- `1994-1995` quedan fuera porque son años parciales
- `1996-1998` quedan fuera del mapa contemporáneo porque usan regiones históricas no equivalentes 1 a 1
- `1999-2024` entran al mapa general
- `2001-2024` entran al mapa de minería
"""
    ),
    code(
        """display(Markdown(
    f'''
**Años completos en la base:** {min(anios_completos)}-{max(anios_completos)}  
**Años de mapas generales:** {min(anios_mapa_general)}-{max(anios_mapa_general)}  
**Años de mapa de minería:** {min(anios_mapa_mineria)}-{max(anios_mapa_mineria)}
'''
))
resumen_anual
"""
    ),
    code(
        """territorio_mapeado = territorio_raw.merge(
    equiv[['territorio_fuente', 'territorio_mapa', 'territorio_label_mapa']],
    left_on='categoria_homologada_agregada',
    right_on='territorio_fuente',
    how='left'
)

base_general = (
    territorio_mapeado[
        territorio_mapeado['anio'].isin(anios_mapa_general)
        & territorio_mapeado['territorio_mapa'].notna()
    ]
    .groupby(['anio', 'territorio_mapa', 'territorio_label_mapa'], as_index=False)[
        ['huelgas', 'trabajadores_comprendidos', 'horas_hombre_perdidas']
    ]
    .sum()
)

territorios_mapa = geo_map[['territorio_mapa', 'territorio_label']].drop_duplicates()
grilla_general = (
    pd.MultiIndex.from_product(
        [anios_mapa_general, territorios_mapa['territorio_mapa']],
        names=['anio', 'territorio_mapa']
    )
    .to_frame(index=False)
    .merge(territorios_mapa, on='territorio_mapa', how='left')
)

mapa_general = (
    grilla_general.merge(
        base_general,
        left_on=['anio', 'territorio_mapa', 'territorio_label'],
        right_on=['anio', 'territorio_mapa', 'territorio_label_mapa'],
        how='left'
    )
    .drop(columns=['territorio_label_mapa'])
    .fillna({
        'huelgas': 0,
        'trabajadores_comprendidos': 0,
        'horas_hombre_perdidas': 0,
    })
    .sort_values(['anio', 'territorio_mapa'])
)

mapa_general.head(12)
"""
    ),
    code(
        """mineria_raw = sector_territorio[
    sector_territorio['anio'].isin(anios_mapa_mineria)
    & sector_territorio['nivel_territorial'].eq('regional')
    & sector_territorio['actividad_homologada_agregada'].eq('mineria')
].copy()

mineria_mapeada = mineria_raw.merge(
    equiv[['territorio_fuente', 'territorio_mapa', 'territorio_label_mapa']],
    left_on='territorio_homologado_agregado',
    right_on='territorio_fuente',
    how='left'
)

base_mineria = (
    mineria_mapeada[mineria_mapeada['territorio_mapa'].notna()]
    .groupby(['anio', 'territorio_mapa', 'territorio_label_mapa'], as_index=False)[
        ['huelgas', 'trabajadores_comprendidos', 'horas_hombre_perdidas']
    ]
    .sum()
)

grilla_mineria = (
    pd.MultiIndex.from_product(
        [anios_mapa_mineria, territorios_mapa['territorio_mapa']],
        names=['anio', 'territorio_mapa']
    )
    .to_frame(index=False)
    .merge(territorios_mapa, on='territorio_mapa', how='left')
)

mapa_mineria = (
    grilla_mineria.merge(
        base_mineria,
        left_on=['anio', 'territorio_mapa', 'territorio_label'],
        right_on=['anio', 'territorio_mapa', 'territorio_label_mapa'],
        how='left'
    )
    .drop(columns=['territorio_label_mapa'])
    .fillna({
        'huelgas': 0,
        'trabajadores_comprendidos': 0,
        'horas_hombre_perdidas': 0,
    })
    .sort_values(['anio', 'territorio_mapa'])
)

mapa_mineria.head(12)
"""
    ),
    md(
        """## Funciones auxiliares

Cada mapa:

- crea una capa por año
- muestra `tooltip` con territorio, año y valor
- agrega selector de año, botones prev/next y botón play
- se guarda como HTML y también se renderiza directo en el notebook
"""
    ),
    code(
        """PALETTES = {
    'huelgas': bcm.linear.YlOrRd_09,
    'trabajadores_comprendidos': bcm.linear.PuBuGn_09,
    'horas_hombre_perdidas': bcm.linear.OrRd_09,
    'mineria': bcm.linear.BuPu_09,
}


def _build_year_control_macro(map_obj, control_id, year_layers, years, initial_year):
    layer_map_js = ',\\n'.join([f'\"{year}\": {layer_name}' for year, layer_name in year_layers.items()])
    years_js = ', '.join([f'\"{year}\"' for year in years])
    template = Template(f'''
    {{% macro html(this, kwargs) %}}
    <div id="{control_id}" style="
        position: fixed;
        top: 10px;
        left: 55px;
        z-index: 9999;
        background: rgba(255,255,255,0.95);
        border: 1px solid #bbb;
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 13px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.18);
    ">
      <div style="font-weight: 700; margin-bottom: 6px;">Año visible</div>
      <div style="display:flex; gap:6px; align-items:center;">
        <button type="button" id="{control_id}_prev">◀</button>
        <select id="{control_id}_select"></select>
        <button type="button" id="{control_id}_next">▶</button>
        <button type="button" id="{control_id}_play">Play</button>
      </div>
    </div>
    {{% endmacro %}}

    {{% macro script(this, kwargs) %}}
    (function() {{
        var map = {map_obj.get_name()};
        var years = [{years_js}];
        var layers = {{
            {layer_map_js}
        }};
        var currentYear = "{initial_year}";
        var timer = null;
        var select = document.getElementById("{control_id}_select");
        var prevBtn = document.getElementById("{control_id}_prev");
        var nextBtn = document.getElementById("{control_id}_next");
        var playBtn = document.getElementById("{control_id}_play");

        years.forEach(function(year) {{
            var option = document.createElement("option");
            option.value = year;
            option.textContent = year;
            select.appendChild(option);
        }});
        select.value = currentYear;

        function showYear(year) {{
            years.forEach(function(y) {{
                if (map.hasLayer(layers[y])) {{
                    map.removeLayer(layers[y]);
                }}
            }});
            layers[year].addTo(map);
            currentYear = year;
            select.value = year;
        }}

        function step(delta) {{
            var idx = years.indexOf(currentYear);
            idx = (idx + delta + years.length) % years.length;
            showYear(years[idx]);
        }}

        select.addEventListener("change", function() {{
            showYear(this.value);
        }});
        prevBtn.addEventListener("click", function() {{
            step(-1);
        }});
        nextBtn.addEventListener("click", function() {{
            step(1);
        }});
        playBtn.addEventListener("click", function() {{
            if (timer) {{
                clearInterval(timer);
                timer = null;
                playBtn.textContent = "Play";
            }} else {{
                timer = setInterval(function() {{
                    step(1);
                }}, 1200);
                playBtn.textContent = "Pause";
            }}
        }});

        showYear(currentYear);
    }})();
    {{% endmacro %}}
    ''')
    macro = MacroElement()
    macro._template = template
    return macro


def render_layered_map(data_df, geo_df, metric, title, outfile, palette_key, years, metric_label):
    palette = PALETTES[palette_key]
    vmax = max(float(data_df[metric].max()), 1.0)
    colormap = palette.scale(0, vmax)
    colormap.caption = metric_label

    m = folium.Map(location=[-9.25, -75.0], zoom_start=5, tiles='CartoDB positron')
    year_layers = {}

    for year in years:
        year_data = data_df[data_df['anio'] == year][['territorio_mapa', 'territorio_label', metric]].copy()
        frame = geo_df.merge(year_data, on='territorio_mapa', how='left')
        frame['territorio_label'] = frame['territorio_label_y'].fillna(frame['territorio_label_x'])
        frame = frame.drop(columns=['territorio_label_x', 'territorio_label_y'])
        frame[metric] = frame[metric].fillna(0)
        frame['fill_color'] = frame[metric].apply(lambda v: colormap(float(v)))
        frame['tooltip_metric'] = frame[metric].map(lambda v: f'{float(v):,.0f}')
        frame['anio_label'] = str(year)

        fg = folium.FeatureGroup(name=str(year), show=(year == years[0]))
        gj = folium.GeoJson(
            data=json.loads(frame.to_json()),
            style_function=lambda feature: {
                'fillColor': feature['properties']['fill_color'],
                'fillOpacity': 0.82,
                'color': '#555555',
                'weight': 0.8,
            },
            highlight_function=lambda _: {
                'weight': 1.6,
                'color': '#111111',
                'fillOpacity': 0.9,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['territorio_label', 'anio_label', 'tooltip_metric'],
                aliases=['Territorio:', 'Año:', f'{metric_label}:'],
                sticky=False,
                labels=True,
            ),
        )
        gj.add_to(fg)
        fg.add_to(m)
        year_layers[year] = fg.get_name()

    title_html = f'''
    <div style="position: fixed; top: 10px; right: 12px; z-index: 9999;
                background-color: rgba(255,255,255,0.92); padding: 10px 14px;
                border: 1px solid #bbb; border-radius: 6px; font-size: 14px;">
        <b>{title}</b>
    </div>
    '''
    m.get_root().html.add_child(Element(title_html))
    m.add_child(_build_year_control_macro(m, f'year_control_{metric}', year_layers, years, years[0]))
    colormap.add_to(m)
    m.save(outfile)
    return m
"""
    ),
    md("## 1. Huelgas por territorio y año"),
    code(
        """outfile_huelgas = OUTPUTS / '01_huelgas_territorio_tiempo.html'
mapa_folium_huelgas = render_layered_map(
    data_df=mapa_general[['anio', 'territorio_mapa', 'territorio_label', 'huelgas']],
    geo_df=geo_map,
    metric='huelgas',
    title='Huelgas por territorio y año (1999-2024)',
    outfile=outfile_huelgas,
    palette_key='huelgas',
    years=anios_mapa_general,
    metric_label='Huelgas',
)
mapa_folium_huelgas
"""
    ),
    md("## 2. Trabajadores comprendidos por territorio y año"),
    code(
        """outfile_trabajadores = OUTPUTS / '02_trabajadores_territorio_tiempo.html'
mapa_folium_trabajadores = render_layered_map(
    data_df=mapa_general[['anio', 'territorio_mapa', 'territorio_label', 'trabajadores_comprendidos']],
    geo_df=geo_map,
    metric='trabajadores_comprendidos',
    title='Trabajadores comprendidos por territorio y año (1999-2024)',
    outfile=outfile_trabajadores,
    palette_key='trabajadores_comprendidos',
    years=anios_mapa_general,
    metric_label='Trabajadores comprendidos',
)
mapa_folium_trabajadores
"""
    ),
    md(
        """## 3. Horas-hombre perdidas por territorio y año

Advertencia: en varios años las horas-hombre pueden incluir arrastre desde el mes anterior y en `2024` incluso desde el año y/o mes anterior.
"""
    ),
    code(
        """outfile_horas = OUTPUTS / '03_horas_hombre_territorio_tiempo.html'
mapa_folium_horas = render_layered_map(
    data_df=mapa_general[['anio', 'territorio_mapa', 'territorio_label', 'horas_hombre_perdidas']],
    geo_df=geo_map,
    metric='horas_hombre_perdidas',
    title='Horas-hombre perdidas por territorio y año (1999-2024)',
    outfile=outfile_horas,
    palette_key='horas_hombre_perdidas',
    years=anios_mapa_general,
    metric_label='Horas-hombre perdidas',
)
mapa_folium_horas
"""
    ),
    md("## 4. Huelgas de minería por territorio y año"),
    code(
        """outfile_mineria = OUTPUTS / '04_mineria_territorio_tiempo.html'
mapa_folium_mineria = render_layered_map(
    data_df=mapa_mineria[['anio', 'territorio_mapa', 'territorio_label', 'huelgas']],
    geo_df=geo_map,
    metric='huelgas',
    title='Huelgas de minería por territorio y año (2001-2024)',
    outfile=outfile_mineria,
    palette_key='mineria',
    years=anios_mapa_mineria,
    metric_label='Huelgas de minería',
)
mapa_folium_mineria
"""
    ),
    md("## Archivos exportados"),
    code(
        """pd.DataFrame(
    {
        'archivo_html': sorted(path.name for path in OUTPUTS.glob('*.html'))
    }
)
"""
    ),
]

nbf.write(nb, NOTEBOOK)
print(f"Notebook rebuilt: {NOTEBOOK}")
