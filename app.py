import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_table
import pandas as pd
import networkx as nx

# Leer archivo Excel
archivo = "proyectos_filtrados.xlsx"
df = pd.read_excel(archivo, sheet_name="relaciones")

# Expandir columnas destino
destino_cols = [col for col in df.columns if col.startswith("Destino")]
df_largo = df.melt(
    id_vars=["Organización origen"],
    value_vars=destino_cols,
    var_name="posicion",
    value_name="colaborador"
).dropna(subset=["colaborador"])

df_largo = df_largo.rename(columns={"Organización origen": "source", "colaborador": "target"})
df_largo["weight"] = 1

# Crear grafo
G = nx.DiGraph()
for _, row in df_largo.iterrows():
    G.add_edge(row["source"], row["target"], weight=row["weight"])

# Cálculo de métricas
pagerank = nx.pagerank(G, weight='weight')
indegree = dict(G.in_degree(weight='weight'))
betweenness = nx.betweenness_centrality(G, weight='weight')

todos_los_destinos = set(df_largo["target"])
todos_los_origenes = set(df_largo["source"])

# Crear lista de nodos con estilo
nodes = []
for node in G.nodes():
    if node in todos_los_destinos:
        size = 25 + pagerank.get(node, 0) * 1000
        color = "#2196f3"  # azul claro
    else:
        size = 20
        color = "#ccc"
    nodes.append({
        'data': {'id': node, 'label': node},
        'classes': 'autor',
        'style': {'width': size, 'height': size, 'background-color': color, 'label': node}
    })

# Crear lista de aristas
edges = []
for source, target in G.edges():
    edges.append({'data': {'source': source, 'target': target}})

# DataFrames de métricas solo para nodos destino
data = []
for node in todos_los_destinos:
    data.append({
        'Organización': node,
        'Grado': indegree.get(node, 0),
        'PageRank': round(pagerank.get(node, 0), 4),
        'InDegree': indegree.get(node, 0),
        'Betweenness': round(betweenness.get(node, 0), 4)
    })
df_metrica = pd.DataFrame(data)

df_metrica1 = df_metrica.sort_values("Grado", ascending=False)
df_metrica2 = df_metrica.sort_values("PageRank", ascending=False)

# App Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Grafo de relaciones entre organizaciones"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=nodes + edges,
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '600px'},
        stylesheet=[
            {'selector': 'node', 'style': {'content': 'data(label)', 'font-size': 12}},
            {'selector': 'edge', 'style': {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'line-color': '#ccc',
                'target-arrow-color': '#ccc'}},
        ]
    ),
    html.Div([
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_metrica1.columns],
            data=df_metrica1.to_dict('records'),
            style_table={'width': '48%', 'display': 'inline-block', 'margin-right': '4%'},
            style_cell={'textAlign': 'left'},
        ),
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_metrica2.columns],
            data=df_metrica2.to_dict('records'),
            style_table={'width': '48%', 'display': 'inline-block'},
            style_cell={'textAlign': 'left'},
        )
    ])
])

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')
