from pathlib import Path

import pandas as pd

if __package__:
    from .config import GROUP_COLUMNS
else:
    from config import GROUP_COLUMNS


def carregar_tabela_tratada(pasta: str | Path = "data/dados_tratados") -> pd.DataFrame:
    """Carrega CSVs tratados e retém somente os campos necessários à previsão."""
    pasta = Path(pasta)
    frames = []
    for path in sorted(pasta.glob("*.csv")):
        columns = pd.read_csv(path, sep=";", nrows=0).columns
        required = {"inicio_semana_notificacao", "unidade_saude", "doenca", "registro_incompleto"}
        if not required.issubset(columns):
            continue
        frame = pd.read_csv(path, sep=";", usecols=list(required))
        frame = frame.loc[~frame["registro_incompleto"].fillna(False)].drop(columns="registro_incompleto")
        frames.append(frame)
    if not frames:
        raise FileNotFoundError(f"Nenhum CSV tratado compatível em {pasta}")
    return construir_tabela_analitica(pd.concat(frames, ignore_index=True))


def construir_tabela_analitica(registros: pd.DataFrame) -> pd.DataFrame:
    """Agrega por semana epidemiológica, unidade e agravo."""
    required = {"inicio_semana_notificacao", "unidade_saude", "doenca"}
    missing = required - set(registros.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    frame = registros[list(required)].copy()
    frame["inicio_semana"] = pd.to_datetime(frame.pop("inicio_semana_notificacao"), errors="coerce")
    frame["unidade_saude"] = frame["unidade_saude"].astype("string").fillna("Não informada")
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
