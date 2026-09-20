from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dash_table, dcc, html

DISEASE_COLORS = {"Dengue": "#edf50b", "Chikungunya": "#65008e", "Zika": "#ff0000"}
RESULT_COLORS = {"Reagente / positivo": "#dc2626", "Não reagente / negativo": "#3b82f6",
                 "Inconclusivo": "#d9a106", "Não realizado": "#94aeb8", "Não informado": "#c592ce"}
CRITERIA_COLORS = {
    "Clínico-epidemiológico": "#ffaa00",  
    "Laboratorial": "#ff0000",           
    "Em investigação": "#b300ff",         
    "Não informado": "#94a3b8"            
}

SEROTYPE_COLORS = {
    "DENV-1": "#f5f10b",                  
    "DENV-2": "#ff7700",                 
    "DENV-3": "#ff0000",                  
    "DENV-4": "#78350f"                   
}
SYMPTOMS = {
    "FEBRE": "Febre", "MIALGIA": "Mialgia", "CEFALEIA": "Cefaleia", "EXANTEMA": "Exantema",
    "VOMITO": "Vômito", "NAUSEA": "Náusea", "DOR_COSTAS": "Dor nas costas", "CONJUNTVIT": "Conjuntivite",
    "ARTRITE": "Artrite", "ARTRALGIA": "Artralgia", "PETEQUIA_N": "Petéquias", "LEUCOPENIA": "Leucopenia",
    "LACO": "Prova do laço", "DOR_RETRO": "Dor retro-orbital",
}
EXAMS = {
    "RESUL_NS1": "NS1", "RESUL_PCR_": "RT-PCR", "RESUL_SORO": "Sorologia IgM (dengue)",
    "RESUL_VI_N": "Isolamento viral", "RES_CHIKS1": "Sorologia IgM chik. (S1)",
    "RES_CHIKS2": "Sorologia IgM chik. (S2)", "RESUL_PRNT": "PRNT",
}
RESULT_LABELS = {"1": "Reagente / positivo", "2": "Não reagente / negativo", "3": "Inconclusivo", "4": "Não realizado"}
CRITERIA_LABELS = {"1": "Laboratorial", "2": "Clínico-epidemiológico", "3": "Em investigação"}
SEROTYPE_LABELS = {"1": "DENV-1", "2": "DENV-2", "3": "DENV-3", "4": "DENV-4"}
# Códigos da ficha SINAN. Dengue/Chikungunya compartilham a mesma ficha (5, 8, 10-13); Zika usa outra (1, 2, 8).
CLASSIFICATION_LABELS = {
    "Dengue": {"5": "Descartado", "8": "Inconclusivo", "10": "Dengue", "11": "Dengue com sinais de alarme",
               "12": "Dengue grave", "13": "Chikungunya"},
    "Chikungunya": {"5": "Descartado", "8": "Inconclusivo", "10": "Dengue", "11": "Dengue com sinais de alarme",
                    "12": "Dengue grave", "13": "Chikungunya"},
    "Zika": {"1": "Zika confirmado", "2": "Descartado", "8": "Inconclusivo"},
}
STATUS_BY_LABEL = {"Descartado": "Descartado", "Inconclusivo": "Inconclusivo"}
INTERVALS = {
    "dias_sintoma_notificacao": "Sintomas → notificação",
    "dias_notificacao_investigacao": "Notificação → investigação",
    "dias_notificacao_encerramento": "Notificação → encerramento",
    "dias_sintoma_encerramento": "Sintomas → encerramento",
}


def _series(frame, column, default):
    return frame[column] if column in frame else pd.Series(default, index=frame.index)


def _code(series):
    """Normaliza códigos que aparecem como '5', '5.0' ou vazio entre os arquivos."""
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True).replace("", pd.NA)


def _date(series):
    """Converte datas em dd/mm/aaaa, aaaa-mm-dd ou serial do Excel (ex.: 45363) para datetime."""
    text = series.astype("string").str.strip()
    serial = pd.to_numeric(text, errors="coerce")
    from_serial = pd.to_datetime(serial, unit="D", origin="1899-12-30", errors="coerce")
    from_text = pd.to_datetime(text.where(serial.isna()), format="mixed", dayfirst=True, errors="coerce")
    return from_serial.fillna(from_text)


def _days(start, end, limit=365):
    days = (end - start).dt.days
    return days.where((days >= 0) & (days <= limit))


def carregar_dados():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    frames = []
    diseases = (("dengue", "Dengue"), ("chik", "Chikungunya"), ("zika", "Zika"), ("zica", "Zika"))

    for path in sorted(data_dir.glob("*.csv")):
        disease = next((label for key, label in diseases if key in path.name.lower()), None)
        if disease is None:
            continue
        source = pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip", dtype=str)
        source.columns = [str(column).strip().upper() for column in source.columns]

        notified = _date(_series(source, "DT_NOTIFIC", pd.NA))
        onset = _date(_series(source, "DT_SIN_PRI", pd.NA))
        investigated = _date(_series(source, "DT_INVEST", pd.NA))
        closed = _date(_series(source, "DT_ENCERRA", pd.NA))
        year = pd.to_numeric(_code(_series(source, "NU_ANO", pd.NA)), errors="coerce").fillna(notified.dt.year)
        week = pd.to_numeric(_code(_series(source, "SEM_NOT", pd.NA)), errors="coerce") % 100
        week = week.fillna(notified.dt.isocalendar().week)

        classification = _code(_series(source, "CLASSI_FIN", pd.NA)).map(CLASSIFICATION_LABELS[disease])
        normalized = pd.DataFrame({
            "doenca": disease,
            "ano": year,
            "semana": week,
            "dt_sintomas": onset,
            "dt_notificacao": notified,
            "classificacao": classification.fillna("Não informado"),
            "criterio": _code(_series(source, "CRITERIO", pd.NA)).map(CRITERIA_LABELS).fillna("Não informado"),
            "sorotipo": _code(_series(source, "SOROTIPO", pd.NA)).map(SEROTYPE_LABELS),
            "dias_sintoma_notificacao": _days(onset, notified),
            "dias_notificacao_investigacao": _days(notified, investigated),
            "dias_notificacao_encerramento": _days(notified, closed),
            "dias_sintoma_encerramento": _days(onset, closed),
        })
        # Caso confirmado = classificação final positiva para a arbovirose (nunca assumir que toda linha é um caso).
        normalized["situacao"] = classification.map(STATUS_BY_LABEL).fillna(
            classification.notna().map({True: "Confirmado", False: "Em investigação / sem classificação"}))
        for column, label in SYMPTOMS.items():
            normalized[f"sintoma_{label}"] = _code(_series(source, column, pd.NA)).map({"1": True, "2": False})
        for column, label in EXAMS.items():
            normalized[f"exame_{label}"] = _code(_series(source, column, pd.NA)).map(RESULT_LABELS).fillna("Não informado")
        frames.append(normalized)

    if not frames:
        raise FileNotFoundError(f"Nenhum dataset encontrado em {data_dir}")
    result = pd.concat(frames, ignore_index=True).dropna(subset=["ano", "semana"])
    result["ano"] = result["ano"].astype(int)
    result["semana"] = result["semana"].astype(int)
    return result


df = carregar_dados()
app = dash.Dash(__name__)
app.title = "Vigilância clínica e laboratorial das arboviroses"
years = sorted(df["ano"].unique())
diseases = sorted(df["doenca"].unique())
statuses = ["Confirmado", "Descartado", "Inconclusivo", "Em investigação / sem classificação"]
symptom_columns = [column for column in df.columns if column.startswith("sintoma_")]
exam_columns = [column for column in df.columns if column.startswith("exame_")]
panel = {"flex": "1", "minWidth": "450px", "backgroundColor": "#fff", "padding": "15px",
         "borderRadius": "10px", "boxShadow": "0 2px 8px rgba(0,0,0,.08)"}
kpi = {**panel, "minWidth": "180px"}


def _options(values):
    return [{"label": str(value), "value": value} for value in values]


def _figure(figure):
    figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 50, "b": 20},
                         legend_title_text="")
    return figure


def _empty(title):
    return _figure(px.scatter(title=title))


app.layout = html.Div(
    style={"backgroundColor": "#f4f6f9", "fontFamily": "Segoe UI, sans-serif", "padding": "25px"},
    children=[
        html.H1("Vigilância clínica e laboratorial das arboviroses", style={"color": "#1e293b"}),
        html.P("Sintomas, critério de confirmação, resultados de exames e prazos de notificação, investigação "
               "e encerramento dos registros de Dengue, Chikungunya e Zika."),
        html.Div([
            html.Div([html.Label("Ano"), dcc.Dropdown(id="filtro-ano", options=_options(years), value=years, multi=True)],
                     style={"flex": "1", "minWidth": "200px"}),
            html.Div([html.Label("Doença"), dcc.Dropdown(id="filtro-doenca", options=_options(diseases), value=diseases, multi=True)],
                     style={"flex": "1", "minWidth": "200px"}),
            html.Div([html.Label("Situação do caso"),
                      dcc.Checklist(id="filtro-situacao", options=_options(statuses), value=statuses, inline=True,
                                    inputStyle={"marginRight": "4px"}, labelStyle={"marginRight": "14px"})],
                     style={"flex": "2", "minWidth": "300px"}),
            html.Div([html.Label("Semana epidemiológica (notificação)"),
                      dcc.RangeSlider(id="filtro-semana", min=1, max=53, step=1, value=[1, 53],
                                      marks={week: str(week) for week in range(1, 54, 4)},
                                      tooltip={"placement": "bottom", "always_visible": False})],
                     style={"flex": "3", "minWidth": "300px"}),
        ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "backgroundColor": "#fff",
                  "padding": "15px", "borderRadius": "10px", "marginBottom": "20px"}),
        html.Div([
            html.Div([html.P("Registros"), html.H2(id="kpi-total")], style=kpi),
            html.Div([html.P("Confirmados"), html.H2(id="kpi-confirmados")], style=kpi),
            html.Div([html.P("Confirmados por laboratório"), html.H2(id="kpi-laboratorio")], style=kpi),
            html.Div([html.P("Mediana sintomas → notificação"), html.H2(id="kpi-notificacao")], style=kpi),
            html.Div([html.P("Mediana notificação → encerramento"), html.H2(id="kpi-encerramento")], style=kpi),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
        html.Br(),
        dcc.Tabs([
            dcc.Tab(label="Sintomas", children=html.Div([
                html.Div(dcc.Graph(id="grafico-sintomas"), style=panel),
                html.Div(dcc.Graph(id="grafico-sintomas-caracteristicos"), style=panel),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "paddingTop": "20px"})),
            dcc.Tab(label="Confirmação diagnóstica", children=html.Div([
                html.Div(dcc.Graph(id="grafico-criterio"), style=panel),
                html.Div(dcc.Graph(id="grafico-classificacao"), style=panel),
                html.Div(dcc.Graph(id="grafico-exames"), style=panel),
                html.Div(dcc.Graph(id="grafico-sorotipo"), style=panel),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "paddingTop": "20px"})),
            dcc.Tab(label="Prazos", children=html.Div([
                html.Div(dcc.Graph(id="grafico-intervalos"), style=panel),
                html.Div(dcc.Graph(id="grafico-intervalos-ano"), style=panel),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "paddingTop": "20px"})),
            dcc.Tab(label="Tabela detalhada", children=html.Div([
                html.P("Registros filtrados pelos controles acima. Use os campos do cabeçalho para filtrar e "
                       "ordenar cada coluna.", style={"color": "#475569"}),
                dash_table.DataTable(
                    id="tabela", page_size=20, sort_action="native", filter_action="native",
                    style_table={"overflowX": "auto"}, style_cell={"fontFamily": "Segoe UI, sans-serif",
                                                                   "fontSize": "13px", "padding": "6px"},
                    style_header={"backgroundColor": "#e2e8f0", "fontWeight": "bold"},
                ),
            ], style={**panel, "marginTop": "20px"})),
        ]),
    ],
)


def _symptom_figures(filtered):
    with_symptoms = filtered.dropna(subset=symptom_columns, how="all")
    if with_symptoms.empty:
        note = "Sem campos de sintomas nos arquivos selecionados (os CSVs de Zika não trazem sinais clínicos)."
        return _empty(note), _empty(note)
    prevalence = (with_symptoms.groupby("doenca")[symptom_columns].mean() * 100).rename(
        columns=lambda column: column.removeprefix("sintoma_"))
    tidy = prevalence.reset_index().melt(id_vars="doenca", var_name="sintoma", value_name="percentual")
    order = prevalence.mean().sort_values().index.tolist()
    symptoms = _figure(px.bar(tidy, y="sintoma", x="percentual", color="doenca", barmode="group", orientation="h",
                              category_orders={"sintoma": order}, color_discrete_map=DISEASE_COLORS,
                              title="Frequência de sintomas por arbovirose (% dos registros com sintomas informados)",
                              labels={"percentual": "% dos registros", "sintoma": "", "doenca": ""}))
    symptoms.update_layout(height=520)

    if len(prevalence) < 2:
        characteristic = _empty("Selecione ao menos duas doenças com sintomas informados para comparar.")
    else:
        others = prevalence.apply(lambda row: prevalence.drop(row.name).mean(), axis=1)
        difference = (prevalence - others).reset_index().melt(id_vars="doenca", var_name="sintoma", value_name="diferenca")
        characteristic = _figure(px.bar(
            difference, y="sintoma", x="diferenca", color="doenca", barmode="group", orientation="h",
            category_orders={"sintoma": order}, color_discrete_map=DISEASE_COLORS,
            title="Sintomas característicos: diferença (p.p.) em relação às demais arboviroses",
            labels={"diferenca": "pontos percentuais acima (+) ou abaixo (−) das demais", "sintoma": "", "doenca": ""}))
        characteristic.update_layout(height=520)
    return symptoms, characteristic


def _confirmation_figures(filtered):
    criteria = filtered.groupby(["doenca", "criterio"]).size().reset_index(name="casos")
    criteria["percentual"] = criteria["casos"] / criteria.groupby("doenca")["casos"].transform("sum") * 100
    criteria_figure = _figure(px.bar(criteria, x="doenca", y="percentual", color="criterio", barmode="stack",
                                     title="Critério de confirmação/descarte por arbovirose",
                                     color_discrete_map=CRITERIA_COLORS,
                                     labels={"percentual": "% dos registros", "doenca": "", "criterio": ""},
                                     hover_data={"casos": True}))

    classification = filtered.groupby(["doenca", "classificacao"]).size().reset_index(name="casos")
    classification_figure = _figure(px.bar(classification, x="classificacao", y="casos", color="doenca", barmode="group",
                                           color_discrete_map=DISEASE_COLORS, title="Classificação final dos registros",
                                           labels={"casos": "Registros", "classificacao": "", "doenca": ""}))

    exams = filtered.melt(id_vars="doenca", value_vars=exam_columns, var_name="exame", value_name="resultado")
    exams["exame"] = exams["exame"].str.removeprefix("exame_")
    exams = exams[exams["resultado"] != "Não informado"].groupby(["exame", "resultado"]).size().reset_index(name="casos")
    if exams.empty:
        exams_figure = _empty("Nenhum resultado de exame informado nos registros selecionados.")
    else:
        exams_figure = _figure(px.bar(exams, x="exame", y="casos", color="resultado", barmode="stack",
                                      color_discrete_map=RESULT_COLORS, title="Resultados dos exames laboratoriais",
                                      category_orders={"resultado": list(RESULT_COLORS)},
                                      labels={"casos": "Exames registrados", "exame": "", "resultado": ""}))

    serotype = filtered.dropna(subset=["sorotipo"]).groupby(["ano", "sorotipo"]).size().reset_index(name="casos")
    if serotype.empty:
        serotype_figure = _empty("Nenhum sorotipo de dengue identificado nos registros selecionados.")
    else:
        serotype_figure = _figure(px.bar(serotype, x="ano", y="casos", color="sorotipo", barmode="stack",
                                         title="Sorotipos de dengue identificados por ano",
                                         color_discrete_map=SEROTYPE_COLORS,
                                         labels={"casos": "Registros", "ano": "", "sorotipo": ""}))
        serotype_figure.update_xaxes(type="category")
    return criteria_figure, classification_figure, exams_figure, serotype_figure


def _interval_figures(filtered):
    intervals = filtered.melt(id_vars=["doenca", "ano"], value_vars=list(INTERVALS), var_name="intervalo",
                              value_name="dias").dropna(subset=["dias"])
    intervals["intervalo"] = intervals["intervalo"].map(INTERVALS)
    if intervals.empty:
        note = "Sem datas válidas para calcular intervalos nos registros selecionados."
        return _empty(note), _empty(note)
    box = _figure(px.box(intervals, x="intervalo", y="dias", color="doenca", color_discrete_map=DISEASE_COLORS,
                         category_orders={"intervalo": list(INTERVALS.values())},
                         title="Intervalos entre sintomas, notificação, investigação e encerramento (dias)",
                         labels={"dias": "Dias", "intervalo": "", "doenca": ""}))
    box.update_yaxes(range=[0, min(120, intervals["dias"].quantile(0.99) + 5)])

    yearly = intervals.groupby(["ano", "doenca", "intervalo"])["dias"].median().reset_index()
    yearly_figure = _figure(px.line(yearly, x="ano", y="dias", color="doenca", line_dash="intervalo", markers=True,
                                    color_discrete_map=DISEASE_COLORS, title="Mediana dos intervalos por ano",
                                    labels={"dias": "Dias (mediana)", "ano": "", "doenca": "", "intervalo": ""}))
    yearly_figure.update_xaxes(type="category")
    return box, yearly_figure


def _table(filtered):
    columns = {
        "doenca": "Doença", "ano": "Ano", "semana": "Semana", "dt_sintomas": "Sintomas",
        "dt_notificacao": "Notificação", "classificacao": "Classificação", "criterio": "Critério",
        "exame_NS1": "NS1", "exame_RT-PCR": "RT-PCR", "exame_Sorologia IgM (dengue)": "Sorologia",
        "exame_Sorologia IgM chik. (S1)": "IgM chik.", "sorotipo": "Sorotipo",
        "dias_sintoma_notificacao": "Dias até notificar", "dias_notificacao_encerramento": "Dias até encerrar",
    }
    table = filtered[list(columns)].rename(columns=columns).sort_values(["Ano", "Semana"], ascending=False)
    for column in ("Sintomas", "Notificação"):
        table[column] = table[column].dt.strftime("%d/%m/%Y")
    table = table.head(5000)
    return table.to_dict("records"), [{"name": name, "id": name} for name in table.columns]


@app.callback(
    Output("kpi-total", "children"), Output("kpi-confirmados", "children"), Output("kpi-laboratorio", "children"),
    Output("kpi-notificacao", "children"), Output("kpi-encerramento", "children"),
    Output("grafico-sintomas", "figure"), Output("grafico-sintomas-caracteristicos", "figure"),
    Output("grafico-criterio", "figure"), Output("grafico-classificacao", "figure"),
    Output("grafico-exames", "figure"), Output("grafico-sorotipo", "figure"),
    Output("grafico-intervalos", "figure"), Output("grafico-intervalos-ano", "figure"),
    Output("tabela", "data"), Output("tabela", "columns"),
    Input("filtro-ano", "value"), Input("filtro-doenca", "value"), Input("filtro-situacao", "value"),
    Input("filtro-semana", "value"),
)
def atualizar_dashboard(selected_years, selected_diseases, selected_statuses, week_range):
    if not selected_years or not selected_diseases or not selected_statuses:
        empty = _empty("Selecione opções nos filtros para visualizar a análise.")
        return "0", "—", "—", "—", "—", *([empty] * 8), [], []
    filtered = df[df["ano"].isin(selected_years) & df["doenca"].isin(selected_diseases) &
                  df["situacao"].isin(selected_statuses) & df["semana"].between(week_range[0], week_range[1])]
    if filtered.empty:
        empty = _empty("Nenhum registro encontrado com os filtros aplicados.")
        return "0", "—", "—", "—", "—", *([empty] * 8), [], []

    confirmed = filtered[filtered["situacao"] == "Confirmado"]
    laboratory = (confirmed["criterio"] == "Laboratorial").mean() * 100 if len(confirmed) else None
    onset_median = filtered["dias_sintoma_notificacao"].median()
    closing_median = filtered["dias_notificacao_encerramento"].median()
    return (
        f"{len(filtered):,}".replace(",", "."),
        f"{len(confirmed):,} ({len(confirmed) / len(filtered) * 100:.1f}%)".replace(",", "."),
        f"{laboratory:.1f}%" if laboratory is not None else "—",
        f"{onset_median:.0f} dias" if pd.notna(onset_median) else "—",
        f"{closing_median:.0f} dias" if pd.notna(closing_median) else "—",
        *_symptom_figures(filtered),
        *_confirmation_figures(filtered),
        *_interval_figures(filtered),
        *_table(filtered),
    )


if __name__ == "__main__":
    app.run(debug=False, port=8055)
