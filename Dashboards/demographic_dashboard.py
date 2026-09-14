from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

DISEASE_COLORS = {"Dengue": "#2563eb", "Chikungunya": "#d97706", "Zika": "#059669"}
SEX_LABELS = {"F": "Feminino", "M": "Masculino", "I": "Ignorado"}
RACE_LABELS = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena", "9": "Ignorado"}

def _series(frame, column, default):
    return frame[column] if column in frame else pd.Series(default, index=frame.index)

def _age(value):
    if pd.isna(value):
        return pd.NA
    try:
        code = int(float(str(value)))
    except (TypeError, ValueError):
        return pd.NA
    prefix, amount = divmod(code, 1000)
    factors = {1: 1 / 8760, 2: 1 / 365, 3: 1 / 12, 4: 1}
    years = amount * factors.get(prefix, 1)
    return years if 0 <= years <= 120 else pd.NA


def carregar_dados():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    frames = []
    diseases = (("dengue", "Dengue"), ("chik", "Chikungunya"), ("zika", "Zika"))

    for path in sorted(data_dir.glob("*.csv")):
        disease = next((label for key, label in diseases if key in path.name.lower()), None)
        if disease is None:
            continue
        source = pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip")
        source.columns = [str(column).strip().upper() for column in source.columns]
        year = pd.to_numeric(_series(source, "NU_ANO", pd.NA), errors="coerce")
        if year.isna().all() and "DT_NOTIFIC" in source:
            year = pd.to_datetime(source["DT_NOTIFIC"], dayfirst=True, errors="coerce").dt.year

        municipality = _series(source, "MUNICIPIO", pd.NA).astype("string").str.strip()
        if municipality.isna().all() or (municipality == "").all():
            municipality = _series(source, "ID_MN_RESI", _series(source, "ID_MUNICIP", "Não informado"))
        municipality = municipality.fillna("Não informado").replace("", "Não informado").astype(str)
        age = pd.to_numeric(_series(source, "NU_IDADE_N", pd.NA).map(_age), errors="coerce")
        normalized = pd.DataFrame({
            "doenca": disease,
            "ano": year,
            "municipio": municipality,
            "idade": age,
            "sexo": _series(source, "CS_SEXO", "I").fillna("I").astype(str).str.upper(),
            "raca": _series(source, "CS_RACA", "9").fillna("9").astype(str).str.replace(r"\.0$", "", regex=True),
            "casos": 1,
        })
        normalized["sexo"] = normalized["sexo"].map(SEX_LABELS).fillna("Não informado")
        normalized["raca"] = normalized["raca"].map(RACE_LABELS).fillna("Não informado")
        normalized["faixa_etaria"] = pd.cut(
            normalized["idade"], [-1, 4, 14, 24, 44, 64, 120],
            labels=["0–4", "5–14", "15–24", "25–44", "45–64", "65+"],
        ).astype("object").fillna("Não informado")
        frames.append(normalized)

    if not frames:
        raise FileNotFoundError(f"Nenhum dataset encontrado em {data_dir}")
    result = pd.concat(frames, ignore_index=True).dropna(subset=["ano"])
    result["ano"] = result["ano"].astype(int)
    return result


df = carregar_dados()
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

    age = filtered.groupby("faixa_etaria", observed=False)["casos"].sum().reset_index()
    sex = filtered.groupby(["sexo", "doenca"])["casos"].sum().reset_index()
    race = filtered.groupby(["raca", "doenca"])["casos"].sum().reset_index()
    yearly = filtered.groupby(["ano", "doenca"])["casos"].sum().reset_index()
    figures = [
        px.bar(age, x="faixa_etaria", y="casos", title="Distribuição por faixa etária"),
        px.bar(sex, x="sexo", y="casos", color="doenca", barmode="group", title="Distribuição por sexo",
               color_discrete_map=DISEASE_COLORS),
        px.bar(race, x="raca", y="casos", color="doenca", barmode="group", title="Distribuição por raça/cor",
               color_discrete_map=DISEASE_COLORS),
        px.line(yearly, x="ano", y="casos", color="doenca", markers=True, title="Evolução anual",
                color_discrete_map=DISEASE_COLORS),
    ]
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
