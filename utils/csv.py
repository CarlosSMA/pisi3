import pandas as pd


def get_data_frame_from_csv_file(file_name):
    print(f"Reading file {file_name}...")
    df = pd.read_csv(
        file_name,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
    )
    return df