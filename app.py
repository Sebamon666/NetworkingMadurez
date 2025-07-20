import pandas as pd
import networkx as nx
import dash
from dash import html, dcc
import dash_cytoscape as cyto
import plotly.graph_objs as go

# Cargar dataset
df = pd.read_excel('proyectos_filtrados.xlsx')

# Crear grafo
G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'])

# Calcular métricas para nodos destino
destinos = set(df['target'])
peso_acumulado = df.groupby('target')['weight'].sum().to_dict()

grado = dict(G.degree(destinos))
pagerank = nx.pagerank(G, weight='weight')
indegree = dict(G.in_degree(destinos, weight='weight'))
betweenness = nx.betweenness_centrality(G)

# Filtrar métricas solo para nodos destino
def filtrar(diccionario):
    return {k: v for k, v in diccionario.items() if k in destinos}

pagerank = filtrar(pagerank)
betweenness = filtrar(betweenness)

# Construcción de nodos y aristas para Cytoscape
nodes = []
for node in G.nodes():
    if node in destinos:
        size = peso_acumulado.get(node, 1) * 20
        color = '#0074D9'
    else:
        size = 20
        color = '#ccc'
    nodes.append({
        'data': {'id': node, 'label': node},
        'classes': 'destino' if node in destinos else 'origen',
        'style': {'background-color': color, 'width': size, 'height': size}
    })

edges = [
    {'data': {'source': u, 'target': v}} for u, v in G.edges()
]

# App Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H2("Red de Conexiones entre Organizaciones"),
    cyto.Cytoscape(
        elements=nodes + edges,
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '600px'},
        stylesheet=[
            {'selector': 'node', 'style': {'label': 'data(label)'}},
            {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle'}}
        ]
    ),
    html.Div([
        dcc.Graph(
            figure=go.Figure(
                data=[go.Bar(x=list(grado.keys()), y=list(grado.values()), marker_color='gray')],
                layout=dict(title='Grado (número de conexiones)', xaxis_title='Organización', yaxis_title='Grado')
            )
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[go.Bar(x=list(pagerank.keys()), y=list(pagerank.values()), marker_color='gray')],
                layout=dict(title='PageRank', xaxis_title='Organización', yaxis_title='Valor')
            )
        )
    ], style={'display': 'flex'}),
    html.Div([
        dcc.Graph(
            figure=go.Figure(
                data=[go.Bar(x=list(indegree.keys()), y=list(indegree.values()), marker_color='gray')],
                layout=dict(title='InDegree', xaxis_title='Organización', yaxis_title='Entradas')
            )
        ),
        dcc.Graph(
            figure=go.Figure(
                data=[go.Bar(x=list(betweenness.keys()), y=list(betweenness.values()), marker_color='gray')],
                layout=dict(title='Betweenness Centrality', xaxis_title='Organización', yaxis_title='Centralidad')
            )
        )
    ], style={'display': 'flex'})
])

if __name__ == '__main__':
    app.run_server(debug=True)
