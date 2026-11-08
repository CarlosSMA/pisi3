import dash
from dash import Input, Output, dcc, html

if __package__:
    from . import clinical_dashboard
    from . import demographic_dashboard
    from . import general_overview
    from . import map_dashboard
    from . import severity_dashboard
else:
    import clinical_dashboard
    import demographic_dashboard
    import general_overview
    import map_dashboard
    import severity_dashboard


app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "VetorRisco - Dashboards"

TAB_STYLE = {
    "padding": "14px 20px",
    "fontWeight": "600",
    "color": "#475569",
    "border": "none",
}
TAB_SELECTED_STYLE = {
    **TAB_STYLE,
    "color": "#2563eb",
    "borderBottom": "3px solid #2563eb",
}

app.layout = html.Div(
    style={
        "backgroundColor": "#f4f6f9",
        "fontFamily": "Segoe UI, sans-serif",
        "minHeight": "100vh",
    },
    children=[
        html.Div(
            style={
                "backgroundColor": "#0f172a",
                "color": "#ffffff",
                "padding": "20px 30px",
            },
            children=[
                html.H1("VetorRisco", style={"margin": "0", "fontSize": "28px"}),
                html.P(
                    "Monitorização interativa das arboviroses",
                    style={"margin": "5px 0 0", "color": "#cbd5e1"},
                ),
            ],
        ),
        dcc.Tabs(
            id="dashboard-tabs",
            value="tab-geral",
            parent_style={
                "backgroundColor": "#ffffff",
                "padding": "0 25px",
                "boxShadow": "0 2px 8px rgba(15, 23, 42, .08)",
            },
            children=[
                dcc.Tab(
                    label="Panorama geral",
                    value="tab-geral",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Clínico",
                    value="tab-clinico",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Gravidade",
                    value="tab-gravidade",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Demográfico",
                    value="tab-demografico",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Geoespacial",
                    value="tab-geoespacial",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
            ],
        ),
        html.Div(id="dashboard-content", style={"padding": "25px"}),
    ],
)


@app.callback(
    Output("dashboard-content", "children"),
    Input("dashboard-tabs", "value"),
)
def render_dashboard(tab):
    dashboards = {
        "tab-geral": general_overview.app.layout,
        "tab-clinico": clinical_dashboard.app.layout,
        "tab-gravidade": severity_dashboard.app.layout,
        "tab-demografico": demographic_dashboard.app.layout,
        "tab-geoespacial": map_dashboard.app.layout,
    }
    return dashboards[tab]


if __name__ == "__main__":
    app.run(debug=False, port=8050)
