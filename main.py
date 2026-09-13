from dash import Dash, html


app = Dash(__name__)
app.title = "Análise epidemiológica"
app.layout = html.Main(
    html.H1("Análise de casos de Dengue, Zika e Chikungunya entre 2023 e 2025")
)


if __name__ == "__main__":
    app.run(debug=True)
