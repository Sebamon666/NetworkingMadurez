import pandas as pd
import networkx as nx
import dash
import dash_cytoscape as cyto
from dash import html
import plotly.graph_objects as go

# Cargar datos
df = pd.read_excel('proyectos_filtrados.xlsx', sheet_name='Networking')
df_largo = df.melt(
    id_vars=["Origen"],
    value_vars=[col for col in df.columns if col.startswith("Destino")],
    var_name="posicion",
    value_name="colaborador"
).dropna(subset=["colaborador"])

df_largo = df_largo.rename(columns={"Origen": "source", "colaborador": "target"})
df_largo["weight"] = 1

# Crear grafo
G = nx.DiGraph()
for _, row in df_largo.iterrows():
    G.add_edge(row["source"], row["target"], weight=row["weight"])

# Identificar nodos
nodos_origen = set(df_largo["source"])
nodos_destino = set(df_largo["target"])
solo_destinos = nodos_destino - nodos_origen

# Calcular métricas solo para nodos destino
in_degree = dict(G.in_degree(weight="weight"))
pagerank = nx.pagerank(G, weight="weight")
betweenness = nx.betweenness_centrality(G)
metricas_df = pd.DataFrame({
    "Organización": list(solo_destinos),
    "Grado": [in_degree.get(n, 0) for n in solo_destinos],
    "PageRank": [pagerank.get(n, 0) for n in solo_destinos],
    "Betweenness": [betweenness.get(n, 0) for n in solo_destinos]
}).sort_values("PageRank", ascending=False)

# Estilos visuales
elementos = []
for node in G.nodes:
    entradas = in_degree.get(node, 0)
    if node in nodos_origen and node not in nodos_destino:
        size = 25
        color = "#66B2FF"
    else:
        size = 25 + entradas * 10
        color = "#FF7F0E"
    elementos.append({
        "data": {"id": node, "label": node},
        "classes": "node",
        "style": {
            "width": size,
            "height": size,
            "background-color": color,
            "label": node,
            "font-size": 10,
            "text-valign": "center",
            "color": "white"
        }
    })

for edge in G.edges(data=True):
    elementos.append({
        "data": {"source": edge[0], "target": edge[1]},
        "classes": "edge"
    })

# App Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    cyto.Cytoscape(
        id='grafo',
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '700px'},
        elements=elementos,
        stylesheet=[
            {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'line-color': '#ccc', 'target-arrow-color': '#ccc'}},
        ]
    ),
    html.Div([
        html.Div([
            html.H4("Grado de Entrada"),
            html.Table([
                html.Tr([html.Th("Organización"), html.Th("Grado")])] +
                [html.Tr([html.Td(row["Organización"]), html.Td(int(row["Grado"]))]) for _, row in metricas_df.iterrows()]
            )
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        html.Div([
            html.H4("PageRank"),
            html.Table([
                html.Tr([html.Th("Organización"), html.Th("PageRank")])] +
                [html.Tr([html.Td(row["Organización"]), html.Td(round(row["PageRank"], 4))]) for _, row in metricas_df.iterrows()]
            )
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
