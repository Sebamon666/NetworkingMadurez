import dash
from dash import dcc, html, dash_table
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx

df = pd.read_excel("proyectos_filtrados.xlsx", sheet_name="Relaciones")
nodos_df = pd.read_excel("proyectos_filtrados.xlsx", sheet_name="Nodos")

df_largo = df.melt(
    id_vars=["Organización origen"],
    value_vars=["Destino.1", "Destino.2", "Destino.3", "Destino.4", "Destino.5"],
    var_name="tipo",
    value_name="colaborador"
).dropna(subset=["colaborador"])

df_largo["colaborador"] = df_largo["colaborador"].str.strip()
df_largo["Organización origen"] = df_largo["Organización origen"].str.strip()

G = nx.DiGraph()
for _, row in df_largo.iterrows():
    G.add_edge(row["Organización origen"], row["colaborador"])

for _, row in nodos_df.iterrows():
    G.add_node(row["Organización"], comunidad=row["Comunidad"])

pagerank = nx.pagerank(G, weight='weight')
indegree = dict(G.in_degree())
betweenness = nx.betweenness_centrality(G)

df_metrics = pd.DataFrame({
    "Organización": list(pagerank.keys()),
    "Grado": indegree.values(),
    "PageRank": pagerank.values(),
    "Betweenness": betweenness.values(),
})
df_metrics = df_metrics[df_metrics["Organización"].isin(df_largo["colaborador"])].copy()

df_metrics = df_metrics.merge(nodos_df, on="Organización", how="left")

community_colors = {
    'Comunidad A': '#FFB6C1',
    'Comunidad B': '#ADD8E6',
    'Comunidad C': '#90EE90',
    'Comunidad D': '#FFD700',
    'Comunidad E': '#FFA07A',
    'Comunidad F': '#D3D3D3',
}

node_styles = []
for node in G.nodes():
    if node in df_largo["Organización origen"].values:
        color = '#B0C4DE'
        size = 20
    else:
        comunidad = nodos_df.loc[nodos_df["Organización"] == node, "Comunidad"].values
        color = community_colors.get(comunidad[0], "#CCCCCC") if comunidad.size > 0 else "#CCCCCC"
        size = 10 + 40 * pagerank.get(node, 0)
    node_styles.append({
        'data': {'id': node, 'label': node},
        'classes': 'autor',
        'style': {'background-color': color, 'width': size, 'height': size}
    })

edges = [{'data': {'source': source, 'target': target}} for source, target in G.edges()]

stylesheet = [
    {'selector': 'node', 'style': {'label': 'data(label)', 'text-wrap': 'wrap', 'text-max-width': 80,
                                   'font-size': 10, 'text-valign': 'center', 'color': '#000'}},
    {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle',
                                   'line-color': '#ccc', 'target-arrow-color': '#ccc'}},
]

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Grafo', children=[
            cyto.Cytoscape(
                id='cytoscape',
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '900px'},
                elements=node_styles + edges,
                stylesheet=stylesheet
            )
        ]),
        dcc.Tab(label='Tablas', children=[
            html.Div([
                html.Div([
                    html.H4("Métricas de Centralidad"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in df_metrics.columns],
                        data=df_metrics.to_dict("records"),
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'fontSize': 12},
                        page_size=20
                    )
                ])
            ])
        ])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8080)
