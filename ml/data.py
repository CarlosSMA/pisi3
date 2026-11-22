from pathlib import Path
from typing import Iterable

import pandas as pd

if __package__:
    from .config import GROUP_COLUMNS
else:
    from config import GROUP_COLUMNS


UNIDADE_NAO_INFORMADA = "Não informada"


def normalizar_codigo_unidade(serie: pd.Series) -> pd.Series:
    """Padroniza o código CNES da unidade com 7 dígitos.

    Nos arquivos de dengue de 2022 e 2023 o código foi exportado como número e
    perdeu os zeros à esquerda ("604" em vez de "0000604"). Sem esta correção a
    mesma unidade aparece como duas entidades diferentes e a série dela parece
    começar apenas em 2024.
    """
    codigos = serie.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True)
    numericos = codigos.str.fullmatch(r"\d{1,7}").fillna(False).astype(bool)
    codigos = codigos.where(~numericos, codigos.str.zfill(7))
    return codigos.replace("", pd.NA).fillna(UNIDADE_NAO_INFORMADA)


def carregar_registros_tratados(
    pasta: str | Path = "data/dados_tratados",
    colunas: Iterable[str] = ("inicio_semana_notificacao", "unidade_saude", "doenca"),
) -> pd.DataFrame:
    """Carrega os registros individuais tratados, sem registros incompletos.

    Apenas as colunas pedidas são lidas. Arquivos que não possuem todas as
    colunas são ignorados.
    """
    pasta = Path(pasta)
    required = set(colunas) | {"registro_incompleto"}
    frames = []
    for path in sorted(pasta.glob("*.csv")):
        columns = pd.read_csv(path, sep=";", nrows=0).columns
        if not required.issubset(columns):
            continue
        frame = pd.read_csv(
            path, sep=";", usecols=list(required), dtype={"unidade_saude": "string"}
        )
        incompleto = frame.pop("registro_incompleto").astype("string").str.lower().eq("true")
        frames.append(frame.loc[~incompleto.fillna(False).astype(bool)])
    if not frames:
        raise FileNotFoundError(f"Nenhum CSV tratado compatível em {pasta}")
    registros = pd.concat(frames, ignore_index=True)
    if "unidade_saude" in registros:
        registros["unidade_saude"] = normalizar_codigo_unidade(registros["unidade_saude"])
    return registros


def carregar_tabela_tratada(pasta: str | Path = "data/dados_tratados") -> pd.DataFrame:
    """Carrega CSVs tratados e retém somente os campos necessários à previsão."""
    return construir_tabela_analitica(carregar_registros_tratados(pasta))


def construir_tabela_analitica(registros: pd.DataFrame) -> pd.DataFrame:
    """Agrega por semana epidemiológica, unidade e agravo."""
    required = {"inicio_semana_notificacao", "unidade_saude", "doenca"}
    missing = required - set(registros.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    frame = registros[list(required)].copy()
    frame["inicio_semana"] = pd.to_datetime(frame.pop("inicio_semana_notificacao"), errors="coerce")
    frame["unidade_saude"] = frame["unidade_saude"].astype("string").fillna(UNIDADE_NAO_INFORMADA)
    frame["doenca"] = frame["doenca"].astype("string").fillna("Não informado")
    frame = frame.dropna(subset=["inicio_semana"])
    if frame.empty:
        raise ValueError("Nenhum registro possui uma semana válida")
    observed = (
        frame.groupby(["inicio_semana", "unidade_saude", "doenca"], as_index=False)
        .size().rename(columns={"size": "novas_notificacoes"})
    )
    rows = []
    for (unit, disease), group in observed.groupby(["unidade_saude", "doenca"], sort=False):
        complete = pd.DataFrame({"inicio_semana": pd.date_range(
            group["inicio_semana"].min(), group["inicio_semana"].max(), freq="7D"
        )})
        complete["unidade_saude"] = unit
        complete["doenca"] = disease
        rows.append(complete.merge(group, how="left", on=GROUP_COLUMNS).fillna({"novas_notificacoes": 0}))
    return pd.concat(rows, ignore_index=True).sort_values(GROUP_COLUMNS).reset_index(drop=True)
