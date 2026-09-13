from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_FILES = {
    f"{disease}-{year}.csv"
    for disease in ("chikungunya", "dengue", "zika")
    for year in range(2022, 2026)
}
ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


@dataclass(frozen=True)
class CsvInventory:
    file: str
    disease: str
    year: int
    encoding: str
    delimiter: str
    columns: list[str]
    column_count: int
    row_count: int
    rows_with_wrong_column_count: int


def discover_csv_files(data_dir: Path) -> list[Path]:
    files = sorted(data_dir.glob("*.csv"))
    names = {file.name for file in files}
    missing = EXPECTED_FILES - names
    if missing:
        raise FileNotFoundError(
            "Arquivos CSV esperados não encontrados: " +
            ", ".join(sorted(missing))
        )
    return [data_dir / name for name in sorted(EXPECTED_FILES)]


def read_text(file: Path) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return file.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Não foi possível decodificar {file}")


def detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t,").delimiter
    except csv.Error:
        return ";"


def inventory_file(file: Path) -> CsvInventory:
    text, encoding = read_text(file)
    delimiter = detect_delimiter(text[:8192])
    rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
    if not rows:
        raise ValueError(f"Arquivo vazio: {file}")

    columns = rows[0]
    expected_width = len(columns)
    wrong_width = sum(len(row) != expected_width for row in rows[1:])
    disease, year_text = file.stem.rsplit("-", maxsplit=1)

    return CsvInventory(
        file=file.name,
        disease=disease,
        year=int(year_text),
        encoding=encoding,
        delimiter=delimiter,
        columns=columns,
        column_count=expected_width,
        row_count=max(len(rows) - 1, 0),
        rows_with_wrong_column_count=wrong_width,
    )


def build_inventory(data_dir: Path) -> list[CsvInventory]:
    return [inventory_file(file) for file in discover_csv_files(data_dir)]


def write_inventory(inventory: Iterable[CsvInventory], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(item) for item in inventory]
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera o inventário estrutural dos CSVs epidemiológicos."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Pasta que contém os 12 CSVs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build") / "inventario_csv.json",
        help="Arquivo JSON de saída do inventário.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inventory = build_inventory(args.data_dir)
    write_inventory(inventory, args.output)
    print(f"Arquivos processados: {len(inventory)}")
    print(f"Inventário gerado em: {args.output}")


if __name__ == "__main__":
    main()
