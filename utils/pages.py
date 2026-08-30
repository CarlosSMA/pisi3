import streamlit as st

from utils import csv


def create_page(page_title, data_file_name):
    st.title(page_title)

    df = csv.get_data_frame_from_csv_file(data_file_name)
    st.dataframe(df)