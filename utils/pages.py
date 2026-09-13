from dash import dash_table, html

from utils import csv


def create_page(page_title, data_file_name):
    df = csv.get_data_frame_from_csv_file(data_file_name)
    return html.Main(
        children=[
            html.H1(page_title),
            dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[
                    {"name": column, "id": column} for column in df.columns
                ],
                page_size=25,
                style_table={"overflowX": "auto"},
            ),
        ]
    )