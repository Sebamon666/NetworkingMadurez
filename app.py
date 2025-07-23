import dash
from dash import html, dcc, Input, Output, dash_table
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx

# === Cargar datos filtrados ===
file_path = "proyectos_filtrados.xlsx"
df_oscs = pd.read_excel(file_path, sheet_name="OSCs")
df_fundaciones = pd.read_excel(file_path, sheet_name="Fundaciones")
df_rel = pd.read_excel(file_path, sheet_name="Proyectos Financiados")

# === Preparar aristas ===
df_aristas = df_rel[['Id de la organización financiera', 'Ids OSC', 'Fondos concedidos']].copy()
df_aristas.columns = ['source', 'target', 'weight']
df_aristas['source'] = df_aristas['source'].astype(str)
df_aristas['target'] = df_aristas['target'].astype(str)

# === Preparar nodos ===
df_oscs['Organización_Id'] = df_oscs['Organización_Id'].astype(str)
df_fundaciones['Organización_Id'] = df_fundaciones['Organización_Id'].astype(str)
df_oscs['tipo'] = 'Donataria'
df_fundaciones['tipo'] = 'Donante'

df_nodos = pd.concat([
    df_oscs[['Organización_Id', 'Organización_Nombre', 'tipo']],
    df_fundaciones[['Organización_Id', 'Organización_Nombre', 'tipo']]
], ignore_index=True)
df_nodos.columns = ['id', 'label', 'tipo']

# === Montos por nodo ===
monto_donado = df_aristas.groupby('source')['weight'].sum().reset_index()
monto_donado.columns = ['id', 'monto_donado']
monto_recibido = df_aristas.groupby('target')['weight'].sum().reset_index()
monto_recibido.columns = ['id', 'monto_recibido']

df_nodos = df_nodos.merge(monto_donado, on='id', how='left')
df_nodos = df_nodos.merge(monto_recibido, on='id', how='left')
df_nodos['monto_donado'] = df_nodos['monto_donado'].fillna(0)
df_nodos['monto_recibido'] = df_nodos['monto_recibido'].fillna(0)

# === Filtrar nodos conectados ===
nodos_validos = df_nodos[
    (df_nodos['monto_donado'] > 0) | (df_nodos['monto_recibido'] > 0)
].copy()

# === Donatarias con ≥2 donantes distintos ===
donaciones_unicas = df_aristas.groupby(['target', 'source']).size().reset_index()
donantes_por_donataria = donaciones_unicas.groupby('target').size().reset_index(name='donantes_unicos')
donantes_por_donataria['target'] = donantes_por_donataria['target'].astype(str)

nodos_validos = nodos_validos.merge(donantes_por_donataria, left_on='id', right_on='target', how='left')
nodos_validos['donantes_unicos'] = nodos_validos['donantes_unicos'].fillna(0)
nodos_validos['destacada'] = (
    (nodos_validos['tipo'] == 'Donataria') &
    (nodos_validos['donantes_unicos'] >= 2)
)

# === Filtrar aristas válidas ===
ids_validos = set(nodos_validos['id'])
aristas_validas = df_aristas[
    df_aristas['source'].isin(ids_validos) &
    df_aristas['target'].isin(ids_validos)
]

# === Construir nodos y aristas ===
nodes = []
for _, row in nodos_validos.iterrows():
    size = max(40, min(100, row['monto_donado'] / 5e5))
    if row['tipo'] == 'Donante':
        size = max(30, min(80, row['monto_donado'] / 1e6))
        label = f"{row['label']}\n${int(row['monto_donado'])}"
    else:
        label = row['label']

    classes = row['tipo'].lower()
    if row['destacada']:
        classes += ' destacada'

    nodes.append({
        'data': {'id': str(row['id']), 'label': label},
        'classes': classes,
        'style': {'width': size, 'height': size}
    })

edges = [{'data': {'source': row['source'], 'target': row['target'], 'weight': row['weight']}} for _, row in aristas_validas.iterrows()]
elements = nodes + edges

# === Tablas ===
grado_donantes = aristas_validas.groupby('source')['target'].nunique().reset_index()
grado_donantes.columns = ['id', 'grado']
grado_donantes['id'] = grado_donantes['id'].astype(str)

tabla_donantes = (
    nodos_validos[nodos_validos['tipo'] == 'Donante']
    .merge(grado_donantes, on='id', how='left')[['label', 'grado']]
    .fillna(0)
    .sort_values(by='grado', ascending=False)
    .head(15)
)

G = nx.DiGraph()
G.add_weighted_edges_from([(row['source'], row['target'], row['weight']) for _, row in aristas_validas.iterrows()])
pagerank_scores = nx.pagerank(G, weight='weight')

tabla_donatarias = nodos_validos[nodos_validos['tipo'] == 'Donataria'].copy()
tabla_donatarias['pagerank'] = tabla_donatarias['id'].map(pagerank_scores).fillna(0)
tabla_donatarias = tabla_donatarias[['label', 'pagerank']].sort_values(by='pagerank', ascending=False).head(15)
tabla_donatarias['pagerank'] = tabla_donatarias['pagerank'].round(6)

# === App ===
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='🔗 Grafo de relaciones', children=[
            html.Div([
                dcc.Input(id='busqueda-nodo', type='text', placeholder='Buscar nodo...', style={'marginRight': '10px'}),
                dcc.Dropdown(
                    id='filtro-tipo',
                    options=[{'label': 'Todas', 'value': 'todos'}, {'label': 'Destacadas', 'value': 'destacada'}],
                    value='todos',
                    clearable=False,
                    style={'width': '200px'}
                )
            ], style={'padding': '10px', 'display': 'flex'}),

            cyto.Cytoscape(
                id='red-donaciones',
                elements=elements,
                layout={'name': 'cose'},
                style={'width': '100vw', 'height': '90vh'},
                stylesheet=[
                    {'selector': 'node', 'style': {'label': 'data(label)', 'color': 'black', 'text-valign': 'center', 'text-halign': 'center', 'font-size': 8}},
                    {'selector': '.donante', 'style': {'background-color': '#0074D9'}},
                    {'selector': '.donataria', 'style': {'background-color': '#FF4136'}},
                    {'selector': '.destacada', 'style': {'background-color': '#B10DC9'}},
                    {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle','width': 'mapData(weight, 100000, 10000000, 0.5, 3)', 'line-color': '#ccc', 'target-arrow-color': '#ccc'}}
                ]
            )
        ]),
        dcc.Tab(label='📊 Tablas resumen', children=[
            html.Div([
                html.Div([
                    html.H4("Top 15 Donantes por Grado"),
                    dash_table.DataTable(
                        data=tabla_donantes.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_donantes.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '5px', 'width': 'auto', 'maxWidth': '200px', 'whiteSpace': 'normal'}
                    )
                ], style={'marginRight': '40px'}),
                html.Div([
                    html.H4("Top 15 Donatarias por PageRank"),
                    dash_table.DataTable(
                        data=tabla_donatarias.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_donatarias.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '5px', 'width': 'auto', 'maxWidth': '200px', 'whiteSpace': 'normal'}
                    )
                ])
            ], style={'display': 'flex', 'padding': '20px'})
        ])
    ])
])

@app.callback(
    Output('red-donaciones', 'elements'),
    Input('busqueda-nodo', 'value'),
    Input('filtro-tipo', 'value')
)
def actualizar_red(busqueda, tipo):
    busqueda = (busqueda or "").strip().lower()
    tipo = tipo.lower()

    nodos_base = []
    for nodo in nodes:
        label = nodo['data']['label'].lower()
        clases = nodo['classes']
        if (not busqueda or busqueda in label) and (tipo == 'todos' or tipo in clases):
            nodos_base.append(nodo['data']['id'])

    nodos_relacionados = set(nodos_base)
    for edge in edges:
        if edge['data']['source'] in nodos_base or edge['data']['target'] in nodos_base:
            nodos_relacionados.update([edge['data']['source'], edge['data']['target']])

    nuevos_nodos = [n for n in nodes if n['data']['id'] in nodos_relacionados]
    nuevos_edges = [e for e in edges if e['data']['source'] in nodos_relacionados and e['data']['target'] in nodos_relacionados]
    return nuevos_nodos + nuevos_edges

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
