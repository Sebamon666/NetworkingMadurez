import dash
from dash import html, dcc, dash_table
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx
import plotly.graph_objs as go

# Leer relaciones
relaciones = pd.read_excel("proyectos_filtrados.xlsx", sheet_name="relaciones")
nodos = pd.read_excel("proyectos_filtrados.xlsx", sheet_name="nodos")

# Construcción del grafo
df_largo = relaciones.melt(
    id_vars=["source"],
    value_vars=["target", "posicion"],
    var_name="tipo",
    value_name="colaborador"
).dropna(subset=["colaborador"])

G = nx.DiGraph()
for _, row in df_largo.iterrows():
    G.add_edge(row["source"], row["colaborador"])

# Calcular métricas solo para nodos destino
destinos = df_largo["colaborador"].unique()
in_degree = nx.in_degree_centrality(G)
betweenness = nx.betweenness_centrality(G)
pagerank = nx.pagerank(G)

data = []
for node in destinos:
    data.append({
        "Organización": node,
        "InDegree": in_degree.get(node, 0),
        "Betweenness": betweenness.get(node, 0),
        "PageRank": pagerank.get(node, 0)
    })
tabla = pd.DataFrame(data).sort_values("PageRank", ascending=False)

# Crear nodos para el grafo
nodos_vis = []
for node in G.nodes():
    if node in relaciones["source"].values:
        color = "#A8C5FF"
        size = 20
    else:
        color = "#3B82F6"
        size = 20 + pagerank.get(node, 0) * 100

    nodos_vis.append({
        'data': {'id': node, 'label': node},
        'style': {'width': size, 'height': size, 'background-color': color, 'font-size': 10}
    })

# Crear aristas
aristas = []
for edge in G.edges():
    aristas.append({
        'data': {'source': edge[0], 'target': edge[1]},
        'classes': 'autoridad'
    })

# App Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H3("Grafo de organizaciones"),
    cyto.Cytoscape(
        id='grafo',
        elements=nodos_vis + aristas,
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '600px'},
        stylesheet=[
            {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center', 'color': '#000'}},
            {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle'}}
        ]
    ),
    html.Div([
        dash_table.DataTable(
            data=tabla[['Organización', 'InDegree']].to_dict('records'),
            columns=[{"name": i, "id": i} for i in ['Organización', 'InDegree']],
            style_table={'width': '45%', 'display': 'inline-block'}
        ),
        dash_table.DataTable(
            data=tabla[['Organización', 'Betweenness']].to_dict('records'),
            columns=[{"name": i, "id": i} for i in ['Organización', 'Betweenness']],
            style_table={'width': '45%', 'display': 'inline-block', 'float': 'right'}
        )
    ])
])

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=10000)
