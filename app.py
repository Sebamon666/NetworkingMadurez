import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table
import pandas as pd
import networkx as nx

df = pd.read_excel("proyectos_filtrados.xlsx", sheet_name="relaciones")

# Transformar a largo
df_largo = df.melt(
    id_vars=["Organización origen"],
    value_vars=["Organización destino 1", "Organización destino 2", "Organización destino 3"],
    var_name="tipo_destino",
    value_name="colaborador"
).dropna(subset=["colaborador"])

# Crear grafo dirigido
G = nx.DiGraph()
for _, row in df_largo.iterrows():
    origen = row["Organización origen"]
    destino = row["colaborador"]
    if G.has_edge(origen, destino):
        G[origen][destino]["weight"] += 1
    else:
        G.add_edge(origen, destino, weight=1)

# Calcular métricas de centralidad
pagerank = nx.pagerank(G, weight='weight')
indegree = dict(G.in_degree(weight='weight'))
betweenness = nx.betweenness_centrality(G, weight='weight')

# Preparar nodos
nodos_df = pd.DataFrame.from_dict(pagerank, orient='index', columns=['PageRank'])
nodos_df["InDegree"] = pd.Series(indegree)
nodos_df["Betweenness"] = pd.Series(betweenness)
nodos_df = nodos_df.reset_index().rename(columns={"index": "Organización"})
nodos_df = nodos_df[~nodos_df["Organización"].isin(df_largo["Organización origen"].unique())]

# Escalar tamaño por PageRank solo para nodos destino
def escala(valor, min_v, max_v, min_out=20, max_out=70):
    if max_v - min_v == 0:
        return (min_out + max_out) / 2
    return min_out + ((valor - min_v) / (max_v - min_v)) * (max_out - min_out)

pagerank_min, pagerank_max = nodos_df["PageRank"].min(), nodos_df["PageRank"].max()

# Armar nodos con color distinto según si es origen o destino
nodes = []
for node in G.nodes():
    is_origen = node in df_largo["Organización origen"].unique()
    color = "#b0c4de" if is_origen else "#7E57C2"
    size = 30 if is_origen else escala(pagerank[node], pagerank_min, pagerank_max)
    nodes.append({
        'data': {'id': node, 'label': node},
        'classes': 'origen' if is_origen else 'destino',
        'style': {'background-color': color, 'width': size, 'height': size, 'label': node}
    })

edges = [
    {'data': {'source': u, 'target': v, 'weight': d['weight']}}
    for u, v, d in G.edges(data=True)
]

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=nodes + edges,
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '700px'},
        stylesheet=[
            {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center', 'color': 'black'}},
            {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'line-color': '#ccc'}}
        ]
    ),
    html.Div([
        dash_table.DataTable(
            columns=[
                {'name': 'Organización', 'id': 'Organización'},
                {'name': 'InDegree', 'id': 'InDegree'},
                {'name': 'PageRank', 'id': 'PageRank'},
                {'name': 'Betweenness', 'id': 'Betweenness'}
            ],
            data=nodos_df.sort_values("PageRank", ascending=False).to_dict("records"),
            style_table={'overflowX': 'auto', 'width': '48%', 'display': 'inline-block'},
            style_cell={'textAlign': 'left', 'fontFamily': 'Arial', 'fontSize': 12},
        ),
        dash_table.DataTable(
            columns=[
                {'name': 'Organización', 'id': 'Organización'},
                {'name': 'InDegree', 'id': 'InDegree'},
                {'name': 'PageRank', 'id': 'PageRank'},
                {'name': 'Betweenness', 'id': 'Betweenness'}
            ],
            data=nodos_df.sort_values("InDegree", ascending=False).to_dict("records"),
            style_table={'overflowX': 'auto', 'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'},
            style_cell={'textAlign': 'left', 'fontFamily': 'Arial', 'fontSize': 12},
        )
    ])
])

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)
