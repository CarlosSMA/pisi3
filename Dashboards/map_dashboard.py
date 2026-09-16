import json
import re
import urllib.request
from pathlib import Path

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px


def carregar_geojson_recife():
    url = "https://raw.githubusercontent.com/gvanrossum/geojson-recife/master/bairros.json"
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None


geojson_bairros = carregar_geojson_recife()


def carregar_dados():
    pasta_script = Path(__file__).resolve().parent
    pasta_dados = pasta_script.parent / \
        'data' if (pasta_script.parent /
                   'data').exists() else pasta_script / 'data'

    if not pasta_dados.exists():
        raise FileNotFoundError(
            f"Pasta de dados não encontrada em: {pasta_dados}")

    dfs = []
    diseases = [('dengue', 'Dengue'),
                ('chik', 'Chikungunya'), ('zika', 'Zika')]

    for caminho in pasta_dados.glob('*.csv'):
        doenca = next(
            (label for key, label in diseases if key in caminho.name.lower()), None)
        if not doenca:
            continue

        df = pd.read_csv(caminho, sep=None, engine='python',
                         on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['doenca'] = doenca

        df['ano'] = pd.to_numeric(df.get('NU_ANO'), errors='coerce')
        if df['ano'].isna().all() and 'DT_NOTIFIC' in df:
            df['ano'] = pd.to_datetime(
                df['DT_NOTIFIC'], errors='coerce').dt.year
        df['ano'] = df['ano'].fillna(2024)

        col_mun_resi = next(
            (c for c in ['ID_MN_RESI', 'MUNICIPIO', 'NM_MUNICIP'] if c in df), None)
        df['mun_residencia'] = df[col_mun_resi].astype(str).replace(
            {'261160': 'Recife', '261160.0': 'Recife'}) if col_mun_resi else 'Recife'

        col_mun_notic = next(
            (c for c in ['ID_MUNICIP', 'MUN_NOTIF', 'ID_MN_NOT'] if c in df), None)
        df['mun_notificacao'] = df[col_mun_notic].astype(str).replace(
            {'261160': 'Recife', '261160.0': 'Recife'}) if col_mun_notic else df['mun_residencia']

        col_unidade = next(
            (c for c in ['ID_UNIDADE', 'NM_UNIDADE', 'UNIDADE'] if c in df), None)
        if col_unidade:
            df['unidade_saude'] = df[col_unidade].fillna(
                'Não informada').astype(str).str.strip().str.title()
        else:
            df['unidade_saude'] = 'Não informada'

        col_bairro = next(
            (c for c in ['NM_BAIRRO', 'ID_BAIRRO', 'BAIRRO', 'NM_LOGRADO'] if c in df), None)
        if col_bairro:
            df['bairro'] = df[col_bairro].fillna(
                'Não informado').astype(str).str.strip().str.title()
        else:
            df['bairro'] = 'Não informado'

        df['casos'] = 1

        cols = ['doenca', 'ano', 'mun_residencia',
                'mun_notificacao', 'unidade_saude', 'bairro', 'casos']
        dfs.append(df[cols])

    df_final = pd.concat(dfs, ignore_index=True).dropna(subset=['ano'])
    df_final['ano'] = df_final['ano'].astype(int)
    return df_final


df = carregar_dados()

app = dash.Dash(__name__)
app.title = "Mapa Epidemiológico e Priorização Territorial"

anos = sorted(df['ano'].unique())
doencas = sorted(df['doenca'].unique())
municipios = sorted([str(m) for m in df['mun_residencia'].dropna().unique()])

CARD_STYLE = {
    'backgroundColor': '#ffffff', 'borderRadius': '10px', 'padding': '18px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'textAlign': 'center', 'flex': '1', 'margin': '8px'
}
