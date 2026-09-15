# -*- coding: utf-8 -*-
import json
import urllib.request
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

DISEASE_COLORS = {"Dengue": "#2563eb",
                  "Chikungunya": "#d97706", "Zika": "#059669"}


def _series(frame, column, default):
    return frame[column] if column in frame else pd.Series(default, index=frame.index)


def _corrigir_texto(texto):
    """Trata encoding de caracteres especiais de bases do SINAN/DATASUS."""
    if pd.isna(texto):
        return "Não informado"
    str_texto = str(texto).strip()
    if not str_texto or str_texto.lower() in ("nan", "<na>", "null", "none"):
        return "Não informado"
    try:
        return str_texto.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return str_texto


def _tratar_nome_bairro(val):
    """Garante a formatação correta de bairros e identifica códigos numéricos."""
    texto = _corrigir_texto(val)
    if texto == "Não informado":
        return texto

    texto_limpo = str(texto).replace(".0", "").strip()
    if texto_limpo.isdigit():
        return f"Bairro (Cód. {texto_limpo})"

    return texto_limpo.title()


def carregar_geojson_bairros():
    """Carrega o GeoJSON dos bairros do Recife (local ou repositório remoto)."""
    geojson_path = Path(__file__).resolve().parent.parent / \
        "data" / "bairros_recife.geojson"
    if geojson_path.exists():
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    url = "https://raw.githubusercontent.com/gespacial/recife-geojson/master/bairros.geojson"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def extrair_chave_bairro(geojson):
    """Identifica a propriedade de nome do bairro no arquivo GeoJSON."""
    if not geojson or "features" not in geojson or not geojson["features"]:
        return "properties.bairro"
    props = geojson["features"][0].get("properties", {})
    for key in ["bairro", "NAME_2", "name", "NM_BAIRRO", "bairro_nome", "NAME"]:
        if key in props:
            return f"properties.{key}"
    return "properties.bairro"


def carregar_dados():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    frames = []
    diseases = (("dengue", "Dengue"),
                ("chik", "Chikungunya"), ("zika", "Zika"))

    for path in sorted(data_dir.glob("*.csv")):
        disease = next(
            (label for key, label in diseases if key in path.name.lower()), None)
        if disease is None:
            continue

        try:
            source = pd.read_csv(
                path, sep=None, engine="python", on_bad_lines="skip", encoding="utf-8")
        except (UnicodeDecodeError, Exception):
            source = pd.read_csv(
                path, sep=None, engine="python", on_bad_lines="skip", encoding="iso-8859-1")

        source.columns = [str(column).strip().upper()
                          for column in source.columns]

        year = pd.to_numeric(_series(source, "NU_ANO", pd.NA), errors="coerce")
        if year.isna().all() and "DT_NOTIFIC" in source:
            year = pd.to_datetime(
                source["DT_NOTIFIC"], dayfirst=True, errors="coerce").dt.year

        # 1. Bairro de Residência (Agregação sem expor endereços individuais)
        if "NM_BAIRRO" in source.columns:
            raw_bairro = source["NM_BAIRRO"]
        elif "ID_BAIRRO" in source.columns:
            raw_bairro = source["ID_BAIRRO"]
        else:
            raw_bairro = pd.Series("Não informado", index=source.index)

        bairro_resi = raw_bairro.fillna(
            "Não informado").map(_tratar_nome_bairro)

        # 2. Município de Notificação e Residência
        muni_resi = _series(source, "ID_MN_RESI", "Não informado").astype(
            str).map(_corrigir_texto)
        muni_notific = _series(source, "MUNICIPIO", _series(
            source, "ID_MUNICIP", "Não informado")).astype(str).map(_corrigir_texto)

        # 3. Unidade de Saúde de Atendimento
        unidade_atendimento = _series(
            source, "ID_UNIDADE", "Não informado").astype(str).map(_corrigir_texto)
        uf = _series(source, "SG_UF_NOT", _series(source, "SG_UF", _series(
            source, "ID_RG_RESI", "PE"))).astype(str).str.strip().str.upper()

        normalized = pd.DataFrame({
            "doenca": disease,
            "ano": year,
            "uf": uf,
            "bairro_resi": bairro_resi,
            "muni_resi": muni_resi,
            "muni_notific": muni_notific,
            "unidade_atendimento": unidade_atendimento,
            "casos": 1,
        })
        frames.append(normalized)

    if not frames:
        raise FileNotFoundError(f"Nenhum dataset encontrado em {data_dir}")
    result = pd.concat(frames, ignore_index=True).dropna(subset=["ano"])
    result["ano"] = result["ano"].astype(int)
    return result


df = carregar_dados()
geojson_bairros = carregar_geojson_bairros()
chave_bairro_geojson = extrair_chave_bairro(geojson_bairros)

app = dash.Dash(__name__)
app.title = "Mapa Epidemiológico das Arboviroses"

years = sorted(df["ano"].unique())
diseases = sorted(df["doenca"].unique())

panel = {
    "flex": "1",
    "minWidth": "450px",
    "backgroundColor": "#fff",
    "padding": "15px",
    "borderRadius": "10px",
    "boxShadow": "0 2px 8px rgba(0,0,0,.08)",
}


def _options(values):
    return [{"label": str(value), "value": value} for value in values]


app.layout = html.Div(
    style={"backgroundColor": "#f4f6f9",
           "fontFamily": "Segoe UI, sans-serif", "padding": "25px"},
    children=[
        html.H1("Mapa Epidemiológico das Arboviroses",
                style={"color": "#1e293b"}),
        html.P("Análise da distribuição espacial por Bairro de Residência, Município de Notificação e Unidade de Atendimento."),

        # Filtros Superiores
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Perspectiva de Análise"),
                        dcc.Dropdown(
                            id="filtro-visao",
                            options=[
                                {"label": "Local de Residência (por Bairro)",
                                 "value": "bairro_resi"},
                                {"label": "Município de Notificação",
                                    "value": "muni_notific"},
                                {"label": "Unidade de Saúde (Atendimento)",
                                 "value": "unidade_atendimento"},
                            ],
                            value="bairro_resi",
                            clearable=False,
                        ),
                    ],
                    style={"flex": "1.5", "minWidth": "250px"},
                ),
                html.Div(
                    [html.Label("Ano"), dcc.Dropdown(
                        id="filtro-ano", options=_options(years), value=years, multi=True)],
                    style={"flex": "1", "minWidth": "180px"},
                ),
                html.Div(
                    [html.Label("Doença"), dcc.Dropdown(
                        id="filtro-doenca", options=_options(diseases), value=diseases, multi=True)],
                    style={"flex": "1", "minWidth": "180px"},
                ),
            ],
            style={
                "display": "flex",
                "gap": "20px",
                "flexWrap": "wrap",
                "backgroundColor": "#fff",
                "padding": "15px",
                "borderRadius": "10px",
                "marginBottom": "20px",
            },
        ),

        # Cartões de KPIs
        html.Div(
            [
                html.Div([html.P("Total de notificações"),
                         html.H2(id="total")], style=panel),
                html.Div([html.P("Bairro/Local com maior risco"),
                         html.H2(id="top-local")], style=panel),
                html.Div([html.P("Total de locais mapeados"),
                         html.H2(id="qtd-locais")], style=panel),
                html.Div([html.P("Média de casos por local"),
                         html.H2(id="media-casos")], style=panel),
            ],
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
        ),
        html.Br(),

        # Grade de Gráficos e Mapa
        html.Div(
            [
                html.Div(dcc.Graph(id="grafico-mapa-bairros"), style=panel),
                html.Div(dcc.Graph(id="grafico-agregado-local"), style=panel),
                html.Div(dcc.Graph(id="grafico-evolucao"), style=panel),
                html.Div(dcc.Graph(id="grafico-composicao"), style=panel),
            ],
            style={"display": "flex", "gap": "20px", "flexWrap": "wrap"},
        ),
    ],
)


@app.callback(
    Output("total", "children"),
    Output("top-local", "children"),
    Output("qtd-locais", "children"),
    Output("media-casos", "children"),
    Output("grafico-mapa-bairros", "figure"),
    Output("grafico-agregado-local", "figure"),
    Output("grafico-evolucao", "figure"),
    Output("grafico-composicao", "figure"),
    Input("filtro-visao", "value"),
    Input("filtro-ano", "value"),
    Input("filtro-doenca", "value"),
)
def atualizar_dashboard(selected_vision, selected_years, selected_diseases):
    empty = px.scatter(
        title="Selecione opções nos filtros para visualizar a análise.")
    empty.update_layout(template="plotly_white", margin={
                        "l": 20, "r": 20, "t": 50, "b": 20})

    if not selected_years or not selected_diseases:
        return "0", "—", "—", "—", empty, empty, empty, empty

    filtered = df[df["ano"].isin(selected_years) &
                  df["doenca"].isin(selected_diseases)]

    if filtered.empty:
        empty.update_layout(
            title="Nenhum registro encontrado com os filtros aplicados.")
        return "0", "—", "—", "—", empty, empty, empty, empty

    labels_visao = {
        "bairro_resi": "Bairro de Residência",
        "muni_notific": "Município de Notificação",
        "unidade_atendimento": "Unidade de Atendimento",
    }
    nome_visao = labels_visao.get(selected_vision, "Local")

    local_summary = (
        filtered[filtered[selected_vision] != "Não informado"]
        .groupby(selected_vision)["casos"]
        .sum()
        .reset_index()
        .sort_values("casos", ascending=False)
    )

    if local_summary.empty:
        local_summary = filtered.groupby(selected_vision)["casos"].sum(
        ).reset_index().sort_values("casos", ascending=False)

    yearly = filtered.groupby(["ano", "doenca"])["casos"].sum().reset_index()
    disease_local = filtered.groupby([selected_vision, "doenca"])[
        "casos"].sum().reset_index()

    # Cálculo dos KPIs
    total_casos = len(filtered)
    top_row = local_summary.iloc[0]
    top_local_str = f"{top_row[selected_vision]} ({top_row['casos']:,})".replace(
        ",", ".")
    qtd_locais = len(local_summary)
    media_val = local_summary["casos"].mean() if not local_summary.empty else 0

    # 1. Renderização do Mapa de Risco Espacial por Bairro
    local_summary["bairro_match"] = local_summary[selected_vision].astype(
        str).str.strip().str.upper()

    if selected_vision == "bairro_resi" and geojson_bairros:
        fig_mapa = px.choropleth(
            local_summary,
            geojson=geojson_bairros,
            locations="bairro_match",
            featureidkey=chave_bairro_geojson,
            color="casos",
            color_continuous_scale="Reds",
            title="Mapa de Risco Espacial por Bairro",
            labels={"casos": "Notificações", "bairro_match": "Bairro"},
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
    else:
        top_map_data = local_summary.head(
            15).sort_values("casos", ascending=True)
        fig_mapa = px.bar(
            top_map_data,
            x="casos",
            y=selected_vision,
            orientation="h",
            color="casos",
            color_continuous_scale="Reds",
            title=f"Intensidade de Risco por {nome_visao}",
            labels={"casos": "Casos", selected_vision: ""},
        )

    # 2. Ranking Agregado dos Principais Locais
    top_12_locais = local_summary.head(12).sort_values("casos", ascending=True)
    fig_agregado = px.bar(
        top_12_locais,
        x="casos",
        y=selected_vision,
        orientation="h",
        title=f"Top 12 locais com mais notificações ({nome_visao})",
        labels={"casos": "Total de casos", selected_vision: ""},
    )
    fig_agregado.update_traces(marker_color="#2563eb")

    # 3. Evolução Anual por Doença
    fig_evolucao = px.line(
        yearly,
        x="ano",
        y="casos",
        color="doenca",
        markers=True,
        title="Evolução anual das notificações",
        color_discrete_map=DISEASE_COLORS,
        labels={"ano": "Ano", "casos": "Casos", "doenca": "Doença"},
    )

    # 4. Distribuição por Agente Etiológico nos Locais Críticos
    top_locais_list = local_summary.head(8)[selected_vision].tolist()
    disease_top = disease_local[disease_local[selected_vision].isin(
        top_locais_list)]

    fig_composicao = px.bar(
        disease_top,
        x=selected_vision,
        y="casos",
        color="doenca",
        barmode="stack",
        title=f"Distribuição de doenças nos principais {nome_visao}s",
        color_discrete_map=DISEASE_COLORS,
        labels={selected_vision: "", "casos": "Casos", "doenca": "Doença"},
    )

    figures = [fig_mapa, fig_agregado, fig_evolucao, fig_composicao]
    for figure in figures:
        figure.update_layout(template="plotly_white", margin={
                             "l": 20, "r": 20, "t": 50, "b": 20})

    return (
        f"{total_casos:,}".replace(",", "."),
        top_local_str,
        f"{qtd_locais:,}".replace(",", "."),
        f"{media_val:,.0f}".replace(",", "."),
        *figures,
    )


if __name__ == "__main__":
    app.run(debug=True, port=8053)
