from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

if __package__:
    from .config import K_RANGE, RANDOM_STATE
else:
    from config import K_RANGE, RANDOM_STATE


def avaliar_kmeans(
    componentes: np.ndarray, k_range=K_RANGE, random_state: int = RANDOM_STATE
) -> tuple[int, dict[int, float], dict[int, float]]:
    """Calcula inércia (Elbow) e silhueta para cada quantidade de clusters."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    inertia: dict[int, float] = {}
    silhouette: dict[int, float] = {}
    samples = len(componentes)
    for k in k_range:
        if k >= samples:
            continue
        model = KMeans(n_clusters=k, n_init=20, random_state=random_state)
        labels = model.fit_predict(componentes)
        inertia[k] = float(model.inertia_)
        silhouette[k] = float(silhouette_score(componentes, labels))
    if not silhouette:
        raise ValueError("Dados insuficientes para avaliar clusters")
    # A segmentação operacional deve ter ao menos três grupos. Mantemos a
    # avaliação de k=2 no relatório como referência, mas não a selecionamos.
    elegiveis = {k: score for k, score in silhouette.items() if k > 2}
    if not elegiveis:
        raise ValueError("Dados insuficientes: são necessários ao menos 3 clusters")
    best_k = max(elegiveis, key=elegiveis.get)
    return best_k, inertia, silhouette

def avaliar_dbscan(
    componentes: np.ndarray,
    eps_values: tuple[float, ...] = (0.3, 0.5, 0.8, 1.0, 1.2),
    min_samples: int = 10,
) -> dict[str, Any]:
    """Avalia clusterização baseada em densidade (DBSCAN) testando diferentes raios."""
    from sklearn.cluster import DBSCAN
    from sklearn.metrics import silhouette_score

    resultados: dict[str, Any] = {}
    melhor_silhueta = -1.0
    melhor_eps = None

    for eps in eps_values:
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(componentes)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_outliers = int(np.sum(labels == -1))

        sil = None
        if n_clusters >= 2:
            sil = float(silhouette_score(componentes, labels))
            if sil > melhor_silhueta:
                melhor_silhueta = sil
                melhor_eps = eps

        resultados[str(eps)] = {
            "n_clusters": n_clusters,
            "n_outliers": n_outliers,
            "silhueta": sil,
        }

    return {
        "algoritmo": "DBSCAN",
        "melhor_eps": melhor_eps,
        "melhor_silhueta": melhor_silhueta if melhor_eps is not None else None,
        "detalhes_por_eps": resultados,
    }

def treinar_classificador(
    componentes: np.ndarray,
    alvo: pd.Series,
    random_state: int = RANDOM_STATE,
) -> tuple[Any, int, dict[str, Any]]:
    """Seleciona k, treina K-Means e cria rótulos ordenados por volume médio."""
    from sklearn.cluster import KMeans

    best_k, inertia, silhouette = avaliar_kmeans(componentes, random_state=random_state)
    model = KMeans(n_clusters=best_k, n_init=20, random_state=random_state)
    relatorio_dbscan = avaliar_dbscan(componentes)
    cluster_ids = model.fit_predict(componentes)
    means = pd.Series(alvo.to_numpy()).groupby(cluster_ids).mean().sort_values()
    labels = {
        int(cluster_id): f"Grupo {position + 1} | Média: {mean:.2f}"
        for position, (cluster_id, mean) in enumerate(means.items())
    }
    report = {
        "random_state": random_state,
        "k_selecionado": best_k,
        "criterio_selecao": "maior silhueta entre k > 2",
        "melhor_k_global": max(silhouette, key=silhouette.get),
        "silhueta_melhor_k_global": max(silhouette.values()),
        "inercia_elbow": {str(k): value for k, value in inertia.items()},
        "silhueta_por_k": {str(k): value for k, value in silhouette.items()},
        "silhueta_selecionada": silhouette[best_k],
        "media_alvo_por_grupo": {
            labels[int(cluster_id)]: float(mean) for cluster_id, mean in means.items()
        },
        "comparacao_dbscan": relatorio_dbscan,
    }
    model.cluster_labels_ = labels
    return model, best_k, report


def rotular_clusters(model: Any, componentes: np.ndarray) -> pd.Series:
    """Converte IDs arbitrários do K-Means em rótulos estáveis e legíveis."""
    ids = model.predict(componentes)
    return pd.Series(
        [model.cluster_labels_[int(cluster_id)] for cluster_id in ids],
        index=getattr(componentes, "index", None),
        dtype="string",
    )


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
