"""Classificação operacional da previsão: faixa de volume e capacidade.

A faixa de volume NÃO vem de clusterização. Ela é definida por limiares
históricos (quantis do alvo no treino), como recomenda o
PLANO_PREVISAO_CARGA_TRABALHO.md. A clusterização das unidades de saúde é uma
análise separada, em ``clustering.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

if __package__:
    from .config import FAIXAS_VOLUME, QUANTIS_FAIXA_VOLUME
else:
    from config import FAIXAS_VOLUME, QUANTIS_FAIXA_VOLUME


def definir_limiares_faixa(
    alvo_treino: pd.Series, quantis: tuple[float, ...] = QUANTIS_FAIXA_VOLUME
) -> list[float]:
    """Limiares das faixas a partir das semanas de treino com notificação.

    Cerca de 79% das semanas × unidade × agravo têm zero notificações, então
    quantis sobre todas as semanas colapsariam em zero. Usamos apenas as
    semanas com pelo menos uma notificação.
    """
    positivos = pd.to_numeric(alvo_treino, errors="coerce")
    positivos = positivos[positivos > 0]
    if positivos.empty:
        raise ValueError("O treino não possui semanas com notificações")
    limiares = [float(positivos.quantile(q)) for q in quantis]
    if any(b <= a for a, b in zip(limiares, limiares[1:])):
        raise ValueError(f"Limiares de faixa não são crescentes: {limiares}")
    return limiares


def rotular_faixa_volume(valores, limiares: list[float]) -> pd.Series:
    """baixo ≤ L1 < moderado ≤ L2 < alto ≤ L3 < muito alto."""
    if len(limiares) != len(FAIXAS_VOLUME) - 1:
        raise ValueError("Número de limiares incompatível com FAIXAS_VOLUME")
    valores = np.asarray(valores, dtype=float)
    indices = np.searchsorted(np.asarray(limiares), valores, side="left")
    return pd.Series(np.asarray(FAIXAS_VOLUME, dtype=object)[indices], dtype="string")


def avaliar_faixas(observado: pd.Series, previsto: pd.Series) -> dict[str, object]:
    """Acurácia e matriz de confusão entre faixa observada e faixa prevista."""
    observado = pd.Categorical(observado, categories=FAIXAS_VOLUME)
    previsto = pd.Categorical(previsto, categories=FAIXAS_VOLUME)
    matriz = pd.crosstab(observado, previsto, dropna=False).reindex(
        index=FAIXAS_VOLUME, columns=FAIXAS_VOLUME, fill_value=0
    )
    return {
        "acuracia": float(np.mean(np.asarray(observado) == np.asarray(previsto))),
        "matriz_confusao": {
            "linhas_observado_colunas_previsto": FAIXAS_VOLUME,
            "valores": matriz.astype(int).to_numpy().tolist(),
        },
    }


def classificar_capacidade(previsoes: pd.DataFrame, capacidades: pd.DataFrame) -> pd.DataFrame:
    """Classifica capacidade somente quando fornecida pela instituição."""
    required = {"unidade_saude", "capacidade_semanal"}
    if not required.issubset(capacidades.columns):
        raise ValueError("capacidades requer unidade_saude e capacidade_semanal")
    result = previsoes.merge(
        capacidades[list(required)], on="unidade_saude", how="left", validate="many_to_one"
    )
    capacity = pd.to_numeric(result["capacidade_semanal"], errors="coerce")
    result["capacidade_operacional"] = np.select(
        [capacity.isna(), result["estimativa"] <= capacity, result["estimativa"] <= capacity * 1.2],
        ["não informada", "dentro da capacidade", "atenção"], default="acima da capacidade",
    )
    result["necessidade_reforco"] = result["capacidade_operacional"].eq("acima da capacidade")
    return result
