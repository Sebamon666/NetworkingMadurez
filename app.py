import dash
from dash import html, dcc, Input, Output, dash_table
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx

# === Leer archivo desde GitHub ===
url = "https://github.com/Sebamon666/NetworkingMadurez/raw/main/proyectos_filtrados.xlsx"
df_nodos = pd.read_excel(url, sheet_name="nodos")
df_rel = pd.read_excel(url, sheet_name="relaciones")

# === Construir grafo con NetworkX ===
G = nx.DiGraph()
G.add_weighted_edges_from([(row['source'], row['target'], row['weight']) for _, row in df_rel.iterrows()])

# === Calcular métricas ===
grado = G.degree()
pagerank = nx.pagerank(G, weight='weight')

df_nodos['grado'] = df_nodos['id'].map(dict(grado)).fillna(0).astype(int)
df_nodos['pagerank'] = df_nodos['id'].map(pagerank).fillna(0).round(6)

# === Construir nodos Cytoscape ===
nodes = []
for _, row in df_nodos.iterrows():
    label = f"{row['id']}\nPR: {row['pagerank']}"
    classes = row['tipo']
    nodes.append({
        'data': {'id': row['id'], 'label': label},
        'classes': classes,
        'style': {'width': 40, 'height': 40}
    })

edges = [{'data': {'source': row['source'], 'target': row['target'], 'weight': row['weight']}} for _, row in df_rel.iterrows()]
elements = nodes + edges

# === Tablas resumen ===
tabla_grado = df_nodos[['id', 'grado']].sort_values(by='grado', ascending=False).head(15)
tabla_pagerank = df_nodos[['id', 'pagerank']].sort_values(by='pagerank', ascending=False).head(15)

# === Estilos del grafo ===
stylesheet = [
    {'selector': 'node', 'style': {
        'label': 'data(label)',
        'color': 'black',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': 8
    }},
    {'selector': '.Organización', 'style': {
        'background-color': '#1f77b4'
    }},
    {'selector': '.Colaboradora', 'style': {
        'background-color': '#ff7f0e'
    }},
    {'selector': '.destacada', 'style': {
        'background-color': '#B10DC9'
    }},
    {'selector': 'edge', 'style': {
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle',
        'width': 2,
        'line-color': '#ccc',
        'target-arrow-color': '#ccc'
    }}
]

# === App Dash ===
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='🔗 Grafo de relaciones', children=[
            html.Div([
                dcc.Input(id='busqueda-nodo', type='text', placeholder='Buscar nodo...', style={'marginRight': '10px'}),
                dcc.Dropdown(
                    id='filtro-tipo',
                    options=[
                        {'label': 'Todos', 'value': 'todos'},
                        {'label': 'Organización', 'value': 'Organización'},
                        {'label': 'Colaboradora', 'value': 'Colaboradora'}
                    ],
                    value='todos',
                    clearable=False,
                    style={'width': '200px'}
                )
            ], style={'padding': '10px', 'display': 'flex'}),

            cyto.Cytoscape(
                id='red-colaboracion',
                elements=elements,
                layout={'name': 'cose'},
                style={'width': '100vw', 'height': '90vh'},
                stylesheet=stylesheet
            )
        ]),
        dcc.Tab(label='📊 Tablas resumen', children=[
            html.Div([
                html.Div([
                    html.H4("Top 15 por Grado"),
                    dash_table.DataTable(
                        data=tabla_grado.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_grado.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '5px'}
                    )
                ], style={'marginRight': '40px'}),
                html.Div([
                    html.H4("Top 15 por PageRank"),
                    dash_table.DataTable(
                        data=tabla_pagerank.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_pagerank.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
