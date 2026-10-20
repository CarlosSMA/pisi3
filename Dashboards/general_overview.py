if __package__:
    from .tratamento_dados import carregar_dados_tratados
else:
    from tratamento_dados import carregar_dados_tratados


import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

df = carregar_dados_tratados()

app = dash.Dash(__name__)
app.title = "Panorama Geral das Arboviroses"

opcoes_anos = [{'label': str(ano), 'value': ano} for ano in sorted(df['ano'].unique())]
opcoes_doencas = [{'label': d, 'value': d} for d in sorted(df['doenca'].unique())]
opcoes_municipios = [{'label': m, 'value': m} for m in sorted(df['municipio'].unique())]

# Estilos Visuais CSS
card_style = {
    'backgroundColor': '#ffffff',
    'borderRadius': '10px',
    'padding': '18px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
    'textAlign': 'center',
    'flex': '1',
    'margin': '8px'
}

filter_style = {
    'backgroundColor': '#ffffff',
    'borderRadius': '10px',
    'padding': '15px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
    'marginBottom': '20px'
}

app.layout = html.Div(style={'backgroundColor': '#f4f6f9', 'fontFamily': 'Segoe UI, sans-serif', 'padding': '25px'}, children=[

    # Cabeçalho do Dashboard
    html.Div(children=[
        html.H1("🦟 Panorama Geral das Arboviroses", style={'color': '#1e293b', 'marginBottom': '5px'}),
        html.H4("Pergunta Principal: Como os casos evoluíram ao longo do período?", style={'color': '#64748b', 'fontWeight': 'normal', 'marginTop': '0px'})
    ], style={'marginBottom': '20px'}),

    # Painel de Filtros (Ano, Doença e Município)
    html.Div(style=filter_style, children=[
        html.H5("🔍 Filtros de Análise", style={'marginBottom': '12px', 'color': '#334155'}),
        html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}, children=[

            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Ano:", style={'fontWeight': 'bold', 'color': '#475569'}),
                dcc.Dropdown(
                    id='filtro-ano',
                    options=opcoes_anos,
                    value=[op['value'] for op in opcoes_anos],
                    multi=True,
                    placeholder="Selecione o(s) ano(s)"
                )
            ]),

            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Doença:", style={'fontWeight': 'bold', 'color': '#475569'}),
                dcc.Dropdown(
                    id='filtro-doenca',
                    options=opcoes_doencas,
                    value=[op['value'] for op in opcoes_doencas],
                    multi=True,
                    placeholder="Selecione a(s) doença(s)"
                )
            ]),

            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Município:", style={'fontWeight': 'bold', 'color': '#475569'}),
                dcc.Dropdown(
                    id='filtro-municipio',
                    options=opcoes_municipios,
                    value=[op['value'] for op in opcoes_municipios],
                    multi=True,
                    placeholder="Selecione o(s) município(s)"
                )
            ])
        ])
    ]),

    # Cards / KPIs Indicadores
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'margin': '-8px'}, children=[
        html.Div(style=card_style, children=[
            html.P("Total de Casos", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-total-casos', style={'color': '#0f172a', 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Doença Predominante", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-doenca-predominante', style={'color': "#f80303", 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Ano de Maior Ocorrência", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-ano-pico', style={'color': '#d97706', 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Semana Epidemiológica de Pico", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-semana-pico', style={'color': '#dc2626', 'margin': '8px 0 0 0'})
        ])
    ]),

    html.Br(),

    # Área de Gráficos
    html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}, children=[

        # Gráfico 1: Linhas por Semana Epidemiológica
        html.Div(style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}, children=[
            dcc.Graph(id='grafico-linha-semana')
        ]),

        # Gráfico 2: Comparativo de Doenças por Ano
        html.Div(style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}, children=[
            dcc.Graph(id='grafico-barra-ano')
        ])
    ])
])

@app.callback(
    [
        Output('card-total-casos', 'children'),
        Output('card-doenca-predominante', 'children'),
        Output('card-ano-pico', 'children'),
        Output('card-semana-pico', 'children'),
        Output('grafico-linha-semana', 'figure'),
        Output('grafico-barra-ano', 'figure')
    ],
    [
        Input('filtro-ano', 'value'),
        Input('filtro-doenca', 'value'),
        Input('filtro-municipio', 'value')
    ]
)
def atualizar_dashboard(anos, doencas, municipios):
    if not anos or not doencas or not municipios:
        fig_vazia = px.line(title="Selecione opções nos filtros para visualizar a análise.")
        return "0", "-", "-", "-", fig_vazia, fig_vazia

    df_filtrado = df[
        (df['ano'].isin(anos)) &
        (df['doenca'].isin(doencas)) &
        (df['municipio'].isin(municipios))
    ]

    if df_filtrado.empty:
        fig_vazia = px.line(title="Nenhum registro encontrado com os filtros aplicados.")
        return "0", "-", "-", "-", fig_vazia, fig_vazia

    total_casos = df_filtrado['casos'].sum()
    doenca_predominante = df_filtrado.groupby('doenca')['casos'].sum().idxmax()
    ano_pico = df_filtrado.groupby('ano')['casos'].sum().idxmax()
    contagem_semanal = df_filtrado.groupby('semana_epidemiologica')['casos'].sum()
    semana_pico = int(contagem_semanal.idxmax()) if not contagem_semanal.empty else None

    serie = df_filtrado.dropna(subset=['inicio_semana_notificacao'])
    df_semana = serie.groupby(['inicio_semana_notificacao', 'doenca'])['casos'].sum().reset_index()
    if not df_semana.empty:
        semanas = pd.date_range(df_semana['inicio_semana_notificacao'].min(),
                                df_semana['inicio_semana_notificacao'].max(), freq='W-SUN')
        grade = pd.MultiIndex.from_product([semanas, doencas],
                                          names=['inicio_semana_notificacao', 'doenca'])
        df_semana = df_semana.set_index(['inicio_semana_notificacao', 'doenca']).reindex(grade).reset_index()
    fig_linha = px.line(
        df_semana,
        x='inicio_semana_notificacao',
        y='casos',
        color='doenca',
        markers=True,
        title="<b>Evolução Semanal dos Casos por Doença</b>",
        labels={'inicio_semana_notificacao': 'Início da semana de notificação', 'casos': 'Total de Casos', 'doenca': 'Doença'},
        color_discrete_map={'Dengue': '#edf50b', 'Chikungunya': '#65008e', 'Zika': '#ff0000'}
    )
    fig_linha.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(type='date')
    )

    df_ano = df_filtrado.groupby(['ano', 'doenca'])['casos'].sum().reset_index()
    fig_barra = px.bar(
        df_ano,
        x='ano',
        y='casos',
        color='doenca',
        barmode='group',
        title="<b>Comparativo Anual por Doença</b>",
        labels={'ano': 'Ano', 'casos': 'Total de Casos', 'doenca': 'Doença'},
        color_discrete_map={'Dengue': '#edf50b', 'Chikungunya': '#65008e', 'Zika': '#ff0000'}
    )
    fig_barra.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(type='category')
    )

    total_formatado = f"{total_casos:,}".replace(",", ".")
    return total_formatado, str(doenca_predominante), str(ano_pico), (f"Semana {semana_pico}" if semana_pico is not None else "Não informado"), fig_linha, fig_barra

if __name__ == '__main__':
    app.run(debug=False, port=8050)
