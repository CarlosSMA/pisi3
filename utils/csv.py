import os

import pandas as pd


def get_data_frame_from_csv_file(file_name):
    print(f"Reading file {file_name}...")
    df = pd.read_csv(f"{file_name}", on_bad_lines='skip')
    return df