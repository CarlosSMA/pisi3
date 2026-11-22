import json
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import dash_table, dcc, html


PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = PROJECT_ROOT / "metricas_carga.json"

PANEL = {
    "backgroundColor": "#ffffff",
    "borderRadius": "10px",
    "padding": "15px",
    "boxShadow": "0 2px 8px rgba(15, 23, 42, .08)",
}


def carregar_metricas():
    if not METRICS_PATH.exists():
        return None
    with METRICS_PATH.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def _linhas_grupos(metricas, nome_grupo):
    dados = metricas.get("justica", {}).get(nome_grupo, {})
    return [
        {
            "Grupo": grupo,
            "Amostras": valores["amostras"],
            "MAE": round(valores["mae"], 3),
            "RMSE": round(valores["rmse"], 3),
            "Erro percentual": round(valores["erro_percentual"], 2),
            "Viés médio": round(valores["viés_médio"], 3),
            "Média observada": round(valores.get("media_observada", 0), 3),
            "MAE relativo": round(valores.get("mae_relativo", 0), 3),
        }
        for grupo, valores in dados.get("grupos", {}).items()
    ]


def _grafico_barras(linhas, titulo):
    if not linhas:
        return px.bar(title=titulo)
    frame = pd.DataFrame(linhas)
    fig = px.bar(
        frame,
        x="Grupo",
        y="MAE",
        color="Viés médio",
        color_continuous_scale=["#ef4444", "#facc15", "#2563eb"],
        color_continuous_midpoint=0,
        text="MAE",
        title=titulo,
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Erro absoluto médio",
        coloraxis_colorbar_title="Viés",
    )
    return fig


def _selecao_maior_disparidade(linhas, limite=5):
    if not linhas:
        return []
    frame = pd.DataFrame(linhas)
    frame = frame.sort_values("MAE", ascending=False)
    return frame.head(limite).to_dict("records")


def _tabela(id_tabela):
    return dash_table.DataTable(
        id=id_tabela,
        columns=[
            {"name": "Grupo", "id": "Grupo"},
            {"name": "Amostras", "id": "Amostras"},
            {"name": "MAE", "id": "MAE"},
            {"name": "RMSE", "id": "RMSE"},
            {"name": "Erro percentual", "id": "Erro percentual"},
            {"name": "Viés médio", "id": "Viés médio"},
            {"name": "Média observada", "id": "Média observada"},
            {"name": "MAE relativo", "id": "MAE relativo"},
        ],
        data=[],
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#0f172a", "color": "#ffffff", "fontWeight": "600"},
        style_cell={"textAlign": "left", "padding": "10px"},
    )


app = dash.Dash(__name__)
app.title = "Justiça operacional"

app.layout = html.Div(
    style={"backgroundColor": "#f4f6f9", "fontFamily": "Segoe UI, sans-serif", "padding": "25px"},
    children=[
        html.H1("Justiça operacional do modelo", style={"color": "#1e293b"}),
        html.P(
            "Avaliação do desempenho por unidade de saúde e agravo. "
            "A análise não utiliza características individuais protegidas.",
            style={"color": "#64748b"},
        ),
        html.Div(id="justica-aviso"),
        html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                html.Div(
                    [html.P("MAE global"), html.H2(id="justica-mae")],
                    style={**PANEL, "flex": "1", "minWidth": "220px", "textAlign": "center"},
                ),
                html.Div(
                    [html.P("Maior diferença de MAE por unidade"), html.H2(id="justica-diferenca-unidade")],
                    style={**PANEL, "flex": "1", "minWidth": "220px", "textAlign": "center"},
                ),
                html.Div(
                    [html.P("Maior diferença de MAE por agravo"), html.H2(id="justica-diferenca-doenca")],
                    style={**PANEL, "flex": "1", "minWidth": "220px", "textAlign": "center"},
                ),
            ],
        ),
        html.Div(
            style={"display": "flex", "gap": "20px", "flexWrap": "wrap"},
            children=[
                html.Div(
                    [dcc.Graph(id="grafico-mae-unidades"), _tabela("tabela-unidades")],
                    style={**PANEL, "flex": "1", "minWidth": "450px"},
                ),
                html.Div(
                    [dcc.Graph(id="grafico-mae-doencas"), _tabela("tabela-doencas")],
                    style={**PANEL, "flex": "1", "minWidth": "450px"},
                ),
            ],
        ),
    ],
)


def atualizar_dashboard():
    metricas = carregar_metricas()
    if not metricas or "justica" not in metricas:
        aviso = html.Div(
            "Execute o treinamento atualizado antes de visualizar esta análise.",
            style={
                "backgroundColor": "#fff7ed",
                "color": "#9a3412",
                "border": "1px solid #fed7aa",
                "borderRadius": "8px",
                "padding": "12px",
                "marginBottom": "20px",
            },
        )
        vazia = px.bar(title="Dados de justiça ainda não disponíveis")
        return aviso, "—", "—", "—", vazia, vazia, [], []

    justica = metricas["justica"]
    unidades = _linhas_grupos(metricas, "unidade_saude")
    doencas = _linhas_grupos(metricas, "doenca")
    diferenca_unidade = justica["unidade_saude"]["disparidades"]["mae_diferenca"]
    diferenca_doenca = justica["doenca"]["disparidades"]["mae_diferenca"]
    mae_global = metricas["regressao"]["mae"]
    limiar_desempenho = mae_global * 1.5
    unidades_acima = [
        unidade["Grupo"]
        for unidade in unidades
        if unidade["MAE"] > limiar_desempenho
    ]
    unidades_destacadas = _selecao_maior_disparidade(unidades)

    aviso = html.Div(
        "Viés positivo indica subestimação; viés negativo indica superestimação. "
        f"Grupos com menos de 20 amostras não são exibidos. "
        f"{len(unidades_acima)} unidade(s) têm MAE acima de 1,5 vezes o MAE global "
        f"({limiar_desempenho:.3f}).",
        style={
            "backgroundColor": "#eff6ff",
            "color": "#1e3a8a",
            "border": "1px solid #bfdbfe",
            "borderRadius": "8px",
            "padding": "12px",
            "marginBottom": "20px",
        },
    )
    return (
        aviso,
        f"{mae_global:.3f}",
        f"{diferenca_unidade:.3f}",
        f"{diferenca_doenca:.3f}",
        _grafico_barras(unidades_destacadas, "Cinco unidades com maior MAE"),
        _grafico_barras(doencas, "MAE por agravo"),
        unidades,
        doencas,
    )
