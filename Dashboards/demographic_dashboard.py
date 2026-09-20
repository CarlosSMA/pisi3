if __package__:
    from .tratamento_dados import carregar_dados_tratados, substituir_nao_informado_pela_moda
else:
    from tratamento_dados import carregar_dados_tratados, substituir_nao_informado_pela_moda


import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

DISEASE_COLORS = {"Dengue": "#edf50b", "Chikungunya": "#65008e", "Zika": "#ff0000"}
SEX_LABELS = {"F": "Feminino", "M": "Masculino", "I": "Ignorado"}
RACE_LABELS = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena", "9": "Ignorado"}

df = carregar_dados_tratados()
app = dash.Dash(__name__)
app.title = "Perfil demográfico das arboviroses"
years = sorted(df["ano"].unique())
diseases = sorted(df["doenca"].unique())
municipalities = sorted(df["municipio"].unique())
panel = {"flex": "1", "minWidth": "450px", "backgroundColor": "#fff", "padding": "15px",
         "borderRadius": "10px", "boxShadow": "0 2px 8px rgba(0,0,0,.08)"}


def _options(values):
    return [{"label": str(value), "value": value} for value in values]


app.layout = html.Div(
    style={"backgroundColor": "#f4f6f9", "fontFamily": "Segoe UI, sans-serif", "padding": "25px"},
    children=[
        html.H1("Perfil demográfico das arboviroses", style={"color": "#1e293b"}),
        html.P("Análise dos registros de Dengue, Chikungunya e Zika por características demográficas."),
        html.Div([
            html.Div([html.Label("Ano"), dcc.Dropdown(id="filtro-ano", options=_options(years), value=years, multi=True)],
                     style={"flex": "1", "minWidth": "200px"}),
            html.Div([html.Label("Doença"), dcc.Dropdown(id="filtro-doenca", options=_options(diseases), value=diseases, multi=True)],
                     style={"flex": "1", "minWidth": "200px"}),
            html.Div([html.Label("Município"), dcc.Dropdown(id="filtro-municipio", options=_options(municipalities),
                                                             value=municipalities, multi=True)],
                     style={"flex": "1", "minWidth": "200px"}),
        ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "backgroundColor": "#fff",
                  "padding": "15px", "borderRadius": "10px", "marginBottom": "20px"}),
        html.Div([
            html.Div([html.P("Total de registros"), html.H2(id="total")], style=panel),
            html.Div([html.P("Idade mediana"), html.H2(id="idade")], style=panel),
            html.Div([html.P("Sexo predominante"), html.H2(id="sexo")], style=panel),
            html.Div([html.P("Raça/cor predominante"), html.H2(id="raca")], style=panel),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
        html.Br(),
        html.Div([
            html.Div(dcc.Graph(id="grafico-idade"), style=panel),
            html.Div(dcc.Graph(id="grafico-sexo"), style=panel),
            html.Div(dcc.Graph(id="grafico-raca"), style=panel),
            html.Div(dcc.Graph(id="grafico-ano"), style=panel),
        ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
    ],
)


@app.callback(
    Output("total", "children"), Output("idade", "children"), Output("sexo", "children"), Output("raca", "children"),
    Output("grafico-idade", "figure"), Output("grafico-sexo", "figure"),
    Output("grafico-raca", "figure"), Output("grafico-ano", "figure"),
    Input("filtro-ano", "value"), Input("filtro-doenca", "value"), Input("filtro-municipio", "value"),
)
def atualizar_dashboard(selected_years, selected_diseases, selected_municipalities):
    empty = px.scatter(title="Selecione opções nos filtros para visualizar a análise.")
    if not selected_years or not selected_diseases or not selected_municipalities:
        return "0", "—", "—", "—", empty, empty, empty, empty
    filtered = df[df["ano"].isin(selected_years) & df["doenca"].isin(selected_diseases) &
                  df["municipio"].isin(selected_municipalities)]
    if filtered.empty:
        empty.update_layout(title="Nenhum registro encontrado com os filtros aplicados.")
        return "0", "—", "—", "—", empty, empty, empty, empty

    filtered = substituir_nao_informado_pela_moda(filtered, ["faixa_etaria", "sexo", "raca"])
    age = filtered.groupby("faixa_etaria", observed=False)["casos"].sum().reset_index()
    sex_graph = filtered.copy()
    valid_sex = ~sex_graph["sexo"].isin(["Ignorado", "Não informado"])
    sex_mode = sex_graph.loc[valid_sex, "sexo"].mode()
    if not sex_mode.empty:
        sex_graph.loc[~valid_sex, "sexo"] = sex_mode.iat[0]
    sex = sex_graph.groupby(["sexo", "doenca"])["casos"].sum().reset_index()
    race = filtered.groupby(["raca", "doenca"])["casos"].sum().reset_index()
    yearly = filtered.groupby(["ano", "doenca"])["casos"].sum().reset_index()
    figures = [
        px.bar(age, x="faixa_etaria", y="casos", title="Distribuição por Faixa Etária", labels={"faixa_etaria": "Faixa Etária", "casos": "Total de Casos"}),

        px.bar(sex, x="sexo", y="casos", color="doenca", barmode="group", title="Distribuição por sexo",
               color_discrete_map=DISEASE_COLORS, labels={"sexo": "Sexo", "casos": "Total de Casos"}),
        px.bar(race, x="raca", y="casos", color="doenca", barmode="group", title="Distribuição por raça/cor",
               color_discrete_map=DISEASE_COLORS, labels={"raca": "Raça/Cor", "casos": "Total de Casos", "doenca": "Doença"}),
        px.line(yearly, x="ano", y="casos", color="doenca", markers=True, title="Evolução anual",
                color_discrete_map=DISEASE_COLORS, labels={"ano": "Ano", "casos": "Total de Casos", "doenca": "Doença"}),
    ]
    annual_years = sorted(yearly["ano"].unique())
    figures[-1].update_xaxes(tickmode="array", tickvals=annual_years,
                            ticktext=[str(int(year)) for year in annual_years])
    for figure in figures:
        figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 50, "b": 20})
    median = filtered["idade"].median()
    return (
        f"{len(filtered):,}".replace(",", "."),
        f"{median:.0f} anos" if pd.notna(median) else "Não informado",
        filtered["sexo"].mode().iat[0],
        filtered["raca"].mode().iat[0],
        *figures,
    )


if __name__ == "__main__":
    app.run(debug=False, port=8051)
