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
