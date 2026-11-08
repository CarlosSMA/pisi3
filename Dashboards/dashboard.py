import dash
from dash import html

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
    children=[],
)


if __name__ == "__main__":
    app.run(debug=False, port=8050)
