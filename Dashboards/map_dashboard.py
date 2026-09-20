if __package__:
    from .tratamento_dados import carregar_dados_tratados, normalizar_bairro, substituir_nao_informado_pela_moda
else:
    from tratamento_dados import carregar_dados_tratados, normalizar_bairro, substituir_nao_informado_pela_moda

import json
import urllib.request

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px


def carregar_geojson_recife():
    url = "https://raw.githubusercontent.com/gvanrossum/geojson-recife/master/bairros.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            geojson = json.loads(response.read().decode())
            for feature in geojson['features']:
                feature['properties']['nome_normalizado'] = normalizar_bairro(feature['properties'].get('name'))
            return geojson
    except Exception:
        return None


geojson_bairros = carregar_geojson_recife()


df = carregar_dados_tratados()

app = dash.Dash(__name__)
app.title = "Mapa Epidemiológico e Priorização Territorial"

anos = sorted(df['ano'].unique())
doencas = sorted(df['doenca'].unique())
municipios = sorted([str(m) for m in df['mun_residencia'].dropna().unique()])

CARD_STYLE = {
    'backgroundColor': '#ffffff', 'borderRadius': '10px', 'padding': '18px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'textAlign': 'center', 'flex': '1', 'margin': '8px'
}


def criar_dropdown(id_elem, rotulo, lista, multi=True, valor_padrao=None):
    val = valor_padrao if valor_padrao is not None else (
        lista if multi else (lista[0] if lista else None))
    return html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
        html.Label(rotulo, style={'fontWeight': 'bold', 'color': '#475569'}),
        dcc.Dropdown(id=id_elem, options=[{'label': str(x), 'value': x} for x in lista],
                     value=val, multi=multi, placeholder=f"Selecione {rotulo.lower()}")
    ])


kpis = [
    ("Total de Bairros Notificados", "card-total-bairros", "#000000"),
    ("Bairro / Ponto de Pico", "card-bairro-pico", "#dc2626"),
    ("Casos na Localidade Líder", "card-casos-bairro-pico", "#ea580c"),
    ("Média de Casos por Ponto", "card-media-bairro", "#000000")
]

app.layout = html.Div(style={'backgroundColor': '#f4f6f9', 'fontFamily': 'Segoe UI, sans-serif', 'padding': '25px'}, children=[

    html.Div([
        html.H1("🗺️ Mapa Epidemiológico e Priorização Territorial",
                style={'color': '#1e293b', 'marginBottom': '5px'}),
        html.H4("Pergunta Principal: Quais bairros apresentam maior concentração de risco e casos?", style={
                'color': '#64748b', 'fontWeight': 'normal', 'marginTop': '0'})
    ], style={'marginBottom': '20px'}),

    html.Div(style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'padding': '15px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'marginBottom': '20px'}, children=[
        html.H5("🔍 Filtros de Análise Territorial e Origem da Informação",
                style={'marginBottom': '12px', 'color': '#334155'}),
        html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'marginBottom': '10px'}, children=[
            criar_dropdown('filtro-perspectiva', 'Visão Territorial:',
                           ['Bairro de Residência',
                               'Município de Notificação', 'Unidade de Saúde'],
                           multi=False, valor_padrao='Bairro de Residência'),
            criar_dropdown('filtro-ano', 'Ano:', anos),
            criar_dropdown('filtro-doenca', 'Doença:', doencas),
            criar_dropdown('filtro-municipio',
                           'Município de Residência:', municipios)
        ])
    ]),

    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'margin': '-8px'}, children=[
        html.Div(style=CARD_STYLE, children=[
            html.P(tit, style={'color': '#64748b',
                   'fontSize': '14px', 'margin': '0'}),
            html.H2(id=cid, style={'color': cor, 'margin': '8px 0 0 0'})
        ]) for tit, cid, cor in kpis
    ]),

    html.Br(),

    html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}, children=[
        html.Div(dcc.Graph(id='mapa-real-bairros'),
                 style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}),

        html.Div(dcc.Graph(id='grafico-ranking-bairros'),
                 style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'})
    ])
])


@app.callback(
    [
        Output('card-total-bairros', 'children'),
        Output('card-bairro-pico', 'children'),
        Output('card-casos-bairro-pico', 'children'),
        Output('card-media-bairro', 'children'),
        Output('mapa-real-bairros', 'figure'),
        Output('grafico-ranking-bairros', 'figure')
    ],
    [
        Input('filtro-perspectiva', 'value'),
        Input('filtro-ano', 'value'),
        Input('filtro-doenca', 'value'),
        Input('filtro-municipio', 'value')
    ]
)
def atualizar_dashboard(perspectiva, sel_anos, sel_doencas, sel_muns):
    if not sel_anos or not sel_doencas or not sel_muns or not perspectiva:
        fig_v = px.bar(
            title="Selecione opções nos filtros para visualizar a análise.")
        return "0", "-", "0", "0", fig_v, fig_v

    sub = df[df['ano'].isin(sel_anos) & df['doenca'].isin(
        sel_doencas) & df['mun_residencia'].isin(sel_muns)]

    if perspectiva == 'Bairro de Residência':
        col_analise = 'bairro'
        label_analise = 'Bairro'
    elif perspectiva == 'Município de Notificação':
        col_analise = 'mun_notificacao'
        label_analise = 'Município de Notificação'
    else:
        col_analise = 'unidade_saude'
        label_analise = 'Unidade de Saúde'

    sub_filtrado = substituir_nao_informado_pela_moda(sub, [col_analise])

    if sub_filtrado.empty:
        fig_v = px.bar(
            title=f"Nenhum registro de {label_analise.lower()} encontrado com os filtros aplicados.")
        return "0", "-", "0", "0", fig_v, fig_v

    counts = sub_filtrado.groupby(col_analise)['casos'].sum(
    ).reset_index().sort_values(by='casos', ascending=False)

    total_locais = len(counts)
    local_pico = counts.iloc[0][col_analise]
    casos_pico = counts.iloc[0]['casos']
    media_casos = sub_filtrado['casos'].sum(
    ) / total_locais if total_locais > 0 else 0

    nomes_mapa = {feature['properties'].get('nome_normalizado')
                  for feature in (geojson_bairros or {}).get('features', [])}
    usar_mapa = perspectiva == 'Bairro de Residência' and counts[col_analise].isin(nomes_mapa).any()
    if usar_mapa:
        fig_mapa = px.choropleth_map(
            counts,
            geojson=geojson_bairros,
            locations='bairro',
            featureidkey="properties.nome_normalizado",
            color='casos',
            color_continuous_scale="Reds",
            map_style="carto-positron",
            zoom=10.5,
            center={"lat": -8.0476, "lon": -34.8770},
            opacity=0.7,
            title="<b>Mapa Real por Bairros do Recife (Intensidade de Casos)</b>",
            labels={'casos': 'Total de Casos', 'bairro': 'Bairro'}
        )
    else:
        fig_mapa = px.bar(
            counts.head(10),
            x='casos',
            y=col_analise,
            orientation='h',
            title=f"<b>Distribuição de Casos por {label_analise}</b>",
            color='casos',
            color_continuous_scale='Reds',
            labels={'casos': 'Total de Casos', "bairro": 'Bairro', col_analise: label_analise}
        )

    fig_mapa.update_layout(template="plotly_white",
                           margin=dict(l=20, r=20, t=50, b=20))

    top15 = counts.head(15).sort_values(by='casos', ascending=True)

    fig_ranking = px.bar(
        top15,
        x='casos',
        y=col_analise,
        orientation='h',
        text='casos',
        title=f"<b>Ranking Top 15 - {label_analise} (Prioridade de Campo)</b>",
        labels={'casos': 'Total de Casos Notificados',
                col_analise: label_analise},
        color='casos',
        color_continuous_scale='Reds'
    )
    fig_ranking.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False
    )

    return (
        f"{total_locais:,}".replace(",", "."),
        str(local_pico),
        f"{casos_pico:,}".replace(",", "."),
        f"{media_casos:.1f}",
        fig_mapa,
        fig_ranking
    )


if __name__ == '__main__':
    app.run(debug=False, port=8051)
