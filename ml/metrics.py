import numpy as np
import pandas as pd


def calcular_metricas(y_true: pd.Series, predicted: pd.Series) -> dict[str, float]:
    error = np.asarray(y_true, dtype=float) - np.asarray(predicted, dtype=float)
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "erro_percentual": float(np.mean(np.abs(error) / np.maximum(np.asarray(y_true), 1)) * 100),
    }


def calcular_metricas_justica(
    avaliacao: pd.DataFrame,
    coluna_grupo: str,
    minimo_amostras: int = 20,
) -> dict[str, object]:
    """Avalia disparidades de desempenho do modelo dentro de cada grupo operacional."""
    required = {coluna_grupo, "alvo", "previsto_continuo"}
    missing = required - set(avaliacao.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    if minimo_amostras < 1:
        raise ValueError("minimo_amostras deve ser maior ou igual a 1")

    por_grupo: dict[str, dict[str, float | int]] = {}
    for grupo, indices in avaliacao.groupby(coluna_grupo, dropna=False):
        if len(indices) < minimo_amostras:
            continue

        y_true = indices["alvo"].astype(float)
        predicted = indices["previsto_continuo"].astype(float)
        error = y_true - predicted
        absolute_error = error.abs()
        percentual_error = (
            absolute_error / np.maximum(y_true.to_numpy(dtype=float), 1) * 100
        )
        media_observada = float(y_true.mean())
        mae = float(absolute_error.mean())

        por_grupo[str(grupo)] = {
            "amostras": int(len(indices)),
            "mae": mae,
            "rmse": float(np.sqrt(np.mean(error.to_numpy(dtype=float) ** 2))),
            "erro_percentual": float(np.mean(percentual_error)),
            "viés_médio": float(error.mean()),
            "media_observada": media_observada,
            "mae_relativo": float(mae / max(media_observada, 1)),
        }

    grupos_com_dados = list(por_grupo)
    if not grupos_com_dados:
        raise ValueError(
            f"Nenhum grupo em '{coluna_grupo}' possui pelo menos "
            f"{minimo_amostras} amostras"
        )

    mae_por_grupo = [por_grupo[grupo]["mae"] for grupo in grupos_com_dados]
    rmse_por_grupo = [por_grupo[grupo]["rmse"] for grupo in grupos_com_dados]
    vies_por_grupo = [por_grupo[grupo]["viés_médio"] for grupo in grupos_com_dados]

    return {
        "coluna_grupo": coluna_grupo,
        "minimo_amostras": minimo_amostras,
        "grupos": por_grupo,
        "disparidades": {
            "mae_diferenca": float(max(mae_por_grupo) - min(mae_por_grupo)),
            "rmse_diferenca": float(max(rmse_por_grupo) - min(rmse_por_grupo)),
            "vies_maximo_sobrestimacao": float(min(vies_por_grupo)),
            "vies_maximo_subestimacao": float(max(vies_por_grupo)),
        },
    }
