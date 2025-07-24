import dash
from dash import html, dcc, dash_table
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx

url = "https://github.com/Sebamon666/NetworkingMadurez/raw/main/Netgraph%20Madurez.xlsx"
xls = pd.ExcelFile(url)
df_relacion = xls.parse("Relación").dropna(subset=["source", "target"])
df_tipo = xls.parse("Tipo").dropna(subset=["id", "tipo"])

tipo_dict = dict(zip(df_tipo["id"], df_tipo["tipo"]))

conteo_aristas = pd.concat([df_relacion["source"], df_relacion["target"]]).value_counts()

nodos_unicos = list(set(df_relacion["source"]).union(set(df_relacion["target"])))
nodos = []
for nodo in nodos_unicos:
    tipo = tipo_dict.get(nodo, "Desconocido")
    conexiones = conteo_aristas.get(nodo, 0)
    if tipo == "OSC":
        clase = "osc"
    elif tipo == "Colaboradora" and conexiones > 1:
        clase = "colab_mas"
    elif tipo == "Colaboradora" and conexiones == 1:
        clase = "colab_una"
    else:
        clase = "desconocido"
    nodos.append({"data": {"id": nodo, "label": nodo}, "classes": clase})

aristas = [{"data": {"source": r["source"], "target": r["target"]}} for _, r in df_relacion.iterrows()]

G = nx.DiGraph()
G.add_edges_from([(r["source"], r["target"]) for _, r in df_relacion.iterrows()])

colaboradoras = [n for n in G.nodes if tipo_dict.get(n) == "Colaboradora"]
tabla_donantes = pd.DataFrame([(n, G.degree(n)) for n in colaboradoras], columns=["Colaboradora", "Grado"]).sort_values(by="Grado", ascending=False)
tabla_donatarias = pd.DataFrame([(n, round(v, 3)) for n, v in nx.pagerank(G).items() if n in colaboradoras], columns=["Colaboradora", "PageRank"]).sort_values(by="PageRank", ascending=False)

app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Tabs(id="tabs", value='grafo', children=[
        dcc.Tab(label='Grafo de Nodos', value='grafo'),
        dcc.Tab(label='📊 Tablas resumen', value='metricas')
    ]),
    html.Div(id='tabs-content')
])

@app.callback(
    dash.Output('tabs-content', 'children'),
    dash.Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'grafo':
        return html.Div([
            cyto.Cytoscape(
                id='cytoscape',
                elements=nodos + aristas,
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '95vh'},
                zoom=1,
                stylesheet=[
                    {
                        "selector": ".osc",
                        "style": {
                            "background-color": "#DF4AF0",
                            "width": 50, "height": 50,
                            "label": "data(label)",
                            "font-size": "9px",
                            "text-valign": "center",
                            "text-halign": "center",
                            "color": "black"
                        }
                    },
                    {
                        "selector": ".colab_una",
                        "style": {
                            "background-color": "#8189F0",
                            "width": 50, "height": 50,
                            "label": "data(label)",
                            "font-size": "9px",
                            "text-valign": "center",
                            "text-halign": "center",
                            "color": "black"
                        }
                    },
                    {
                        "selector": ".colab_mas",
                        "style": {
                            "background-color": "#4A56F0",
                            "width": 50, "height": 50,
                            "label": "data(label)",
                            "font-size": "9px",
                            "text-valign": "center",
                            "text-halign": "center",
                            "color": "black"
                        }
                    },
                    {
                        "selector": ".desconocido",
                        "style": {
                            "background-color": "#D3D3D3",
                            "width": 50, "height": 50,
                            "label": "data(label)",
                            "font-size": "9px",
                            "text-valign": "center",
                            "text-halign": "center",
                            "color": "black"
                        }
                    },
                    {
                        "selector": "edge",
                        "style": {
                            "curve-style": "bezier",
                            "target-arrow-shape": "triangle",
                            "target-arrow-color": "#999",
                            "line-color": "#999",
                            "arrow-scale": 1
                        }
                    }
                ]
            )
        ])
    elif tab == 'metricas':
        return html.Div([
            html.Div([
                html.Div([
                    html.H4("Grado"),
                    dash_table.DataTable(
                        data=tabla_donantes.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_donantes.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '5px', 'width': 'auto', 'maxWidth': '200px', 'whiteSpace': 'normal'}
                    )
                ], style={'marginRight': '40px'}),
                html.Div([
                    html.H4("PageRank"),
                    dash_table.DataTable(
                        data=tabla_donatarias.to_dict('records'),
                        columns=[{'name': i, 'id': i} for i in tabla_donatarias.columns],
                        style_table={'width': 'fit-content', 'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '5px', 'width': 'auto', 'maxWidth': '200px', 'whiteSpace': 'normal'}
                    )
                ])
            ], style={'display': 'flex', 'padding': '20px'})
        ])

if __name__ == '__main__':
    app.run(debug=False)
