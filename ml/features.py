import pandas as pd

if __package__:
    from .config import BASELINE_COLUMNS
else:
    from config import BASELINE_COLUMNS


def criar_features(tabela: pd.DataFrame, horizonte: int = 1) -> pd.DataFrame:
    """Cria variáveis históricas e o alvo futuro sem vazamento temporal."""
    if horizonte < 1:
        raise ValueError("horizonte deve ser um número de semanas positivo")
    frame = tabela.copy()
    frame["inicio_semana"] = pd.to_datetime(frame["inicio_semana"], errors="coerce")
    frame["novas_notificacoes"] = pd.to_numeric(frame["novas_notificacoes"], errors="coerce").fillna(0)
    grouped = frame.groupby(["unidade_saude", "doenca"], sort=False)["novas_notificacoes"]
    for lag in (1, 2, 4, 8):
        frame[f"lag_{lag}"] = grouped.shift(lag)
    frame["media_4"] = grouped.transform(lambda values: values.shift(1).rolling(4, min_periods=1).mean())
    frame["media_8"] = grouped.transform(lambda values: values.shift(1).rolling(8, min_periods=1).mean())
    frame["tendencia_4"] = frame["lag_1"] - frame["lag_4"]
    frame["ano"] = frame["inicio_semana"].dt.year
    frame["semana"] = frame["inicio_semana"].dt.isocalendar().week.astype(int)
    frame["mes"] = frame["inicio_semana"].dt.month
    frame["periodo_alvo"] = frame.groupby(["unidade_saude", "doenca"])["inicio_semana"].shift(-horizonte)
    frame["alvo"] = frame.groupby(["unidade_saude", "doenca"])["novas_notificacoes"].shift(-horizonte)
    return frame.dropna(subset=["periodo_alvo", "alvo"]).reset_index(drop=True)


def adicionar_baselines(frame: pd.DataFrame) -> pd.DataFrame:
    """Calcula baselines usando somente histórico anterior ao corte."""
    result = frame.copy()
    groups = result.groupby(["unidade_saude", "doenca"], sort=False)
    result["baseline_media_movel"] = result["media_4"]
    result["baseline_semana_anterior"] = result["lag_1"]
    result["baseline_anual"] = groups["novas_notificacoes"].shift(52).fillna(result["media_8"])
    result["baseline_media_historica"] = groups["novas_notificacoes"].transform(
        lambda values: values.shift(1).expanding(min_periods=1).mean()
    )
    return result
