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
app.title = "Gravidade, Hospitalização e Desfechos"

opcoes_anos = [{'label': str(ano), 'value': ano} for ano in sorted(df['ano'].unique())]
opcoes_doencas = [{'label': d, 'value': d} for d in sorted(df['doenca'].unique())]
opcoes_municipios = [{'label': m, 'value': m} for m in sorted(df['municipio'].unique())]


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


    html.Div(children=[
        html.H1("Gravidade, Hospitalização e Desfechos", style={'color': '#1e293b', 'marginBottom': '5px'}),
        html.H4("Quais doenças ou grupos apresentam maior gravidade?", style={'color': '#64748b', 'fontWeight': 'normal', 'marginTop': '0px'})
    ], style={'marginBottom': '20px'}),


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


    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'margin': '-8px'}, children=[
        html.Div(style=card_style, children=[
            html.P("Taxa de Hospitalização", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-taxa-hosp', style={'color': '#ea580c', 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Casos de Alarme / Graves", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-casos-graves', style={'color': '#d97706', 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Óbitos Confirmados", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-obitos', style={'color': "#000000", 'margin': '8px 0 0 0'})
        ]),
        html.Div(style=card_style, children=[
            html.P("Tempo Médio Encerramento", style={'color': '#64748b', 'fontSize': '14px', 'margin': '0'}),
            html.H2(id='card-tempo-medio', style={'color': '#475569', 'margin': '8px 0 0 0'})
        ])
    ]),

    html.Br(),


    html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}, children=[

        # Gráfico 1: Hospitalização por Comorbidade
        html.Div(style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}, children=[
            dcc.Graph(id='grafico-comorbidades')
        ]),

        # Gráfico 2: Gravidade Clínica por Doença
        html.Div(style={'flex': '1', 'minWidth': '450px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}, children=[
            dcc.Graph(id='grafico-gravidade-doenca')
        ])
    ])
])


@app.callback(
    [
        Output('card-taxa-hosp', 'children'),
        Output('card-casos-graves', 'children'),
        Output('card-obitos', 'children'),
        Output('card-tempo-medio', 'children'),
        Output('grafico-comorbidades', 'figure'),
        Output('grafico-gravidade-doenca', 'figure')
    ],
    [
        Input('filtro-ano', 'value'),
        Input('filtro-doenca', 'value'),
        Input('filtro-municipio', 'value')
    ]
)
def atualizar_dashboard(anos, doencas, municipios):
    if not anos or not doencas or not municipios:
        fig_vazia = px.bar(title="Selecione opções nos filtros para visualizar a análise.")
        return "0%", "0", "0", "-", fig_vazia, fig_vazia

    df_filtrado = df[
        (df['ano'].isin(anos)) &
        (df['doenca'].isin(doencas)) &
        (df['municipio'].isin(municipios))
    ]

    if df_filtrado.empty:
        fig_vazia = px.bar(title="Nenhum registro encontrado com os filtros aplicados.")
        return "0%", "0", "0", "-", fig_vazia, fig_vazia


    total_casos = df_filtrado['casos'].sum()
    total_hosp = df_filtrado['hospitalizado'].sum()
    taxa_hosp = df_filtrado['hospitalizado'].mean() * 100

    total_graves = (df_filtrado['sinais_alarme'] | df_filtrado['caso_grave']).sum(min_count=1)
    total_obitos = df_filtrado['obito'].sum(min_count=1)

    tempo_medio = df_filtrado['tempo_encerramento'].dropna().mean()
    tempo_str = f"{tempo_medio:.0f} dias" if pd.notna(tempo_medio) else "N/A"

    # Gráfico 1: Hospitalização por Comorbidade (%)
    comorbidades_dict = {
        'Hipertensão': 'hipertensao',
        'Diabetes': 'diabetes',
        'Doença Renal': 'renal',
        'Hematológica': 'hematologia',
        'Hepatopatia': 'hepatopatia',
        'Autoimune': 'autoimune'
    }

    dados_comorb = []
    for label, col in comorbidades_dict.items():
        sub = df_filtrado[df_filtrado[col] == 1]
        taxa = sub['hospitalizado'].mean() * 100
        taxa = float(taxa) if pd.notna(taxa) else float('nan')
        dados_comorb.append({'Comorbidade': label, 'Taxa Hospitalização (%)': round(taxa, 1), 'Respostas conhecidas': int(sub['hospitalizado'].count())})

    df_comorb_graph = pd.DataFrame(dados_comorb)
    fig_comorb = px.bar(
        df_comorb_graph,
        x='Taxa Hospitalização (%)',
        y='Comorbidade',
        orientation='h',
        text='Taxa Hospitalização (%)',
        title="<b>Taxa de Hospitalização por Comorbidade</b>",
        labels={'Taxa Hospitalização (%)': 'Taxa de Hospitalização (%)', 'Comorbidade': 'Comorbidade'},
        color='Taxa Hospitalização (%)',
        color_continuous_scale='Reds'
    )
    fig_comorb.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False
    )

    # Gráfico 2: Gravidade Clínica por Doença (Barras Agrupadas)
    df_grav = df_filtrado.groupby('doenca')[['sinais_alarme', 'caso_grave', 'obito']].sum(min_count=1).reset_index()
    df_grav_melt = df_grav.melt(id_vars=['doenca'], value_vars=['sinais_alarme', 'caso_grave', 'obito'],
                                 var_name='Classificação', value_name='Casos')

    mapa_labels = {'sinais_alarme': 'Sinais de Alarme', 'caso_grave': 'Casos Graves', 'obito': 'Óbitos'}
    df_grav_melt['Classificação'] = df_grav_melt['Classificação'].map(mapa_labels)

    fig_grav = px.bar(
        df_grav_melt,
        x='doenca',
        y='Casos',
        color='Classificação',
        barmode='group',
        title="<b>Complicações e Gravidade Clínica por Doença</b>",
        labels={'doenca': 'Doença', 'Casos': 'Total de Casos', 'Classificação': 'Tipo'},
        color_discrete_map={'Sinais de Alarme': "#e08f04", 'Casos Graves': '#dc2626', 'Óbitos': '#000000'}
    )
    fig_grav.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return (f"{taxa_hosp:.1f}%" if pd.notna(taxa_hosp) else "Não informado"), (f"{total_graves:,}".replace(",", ".") if pd.notna(total_graves) else "Não disponível"), (f"{total_obitos:,}".replace(",", ".") if pd.notna(total_obitos) else "Não informado"), tempo_str, fig_comorb, fig_grav


if __name__ == '__main__':
    app.run(debug=False, port=8053)
