"""Gráficos de regressão e blocos de volume previstos."""

from pathlib import Path

import numpy as np
import pandas as pd

BLOCK_COLORS = ["#2c7fb8", "#41ab5d", "#fdae61", "#d7191c", "#8073ac", "#e08214", "#1b9e77", "#e7298a"]


def _pyplot():
    import matplotlib.pyplot as plt

    return plt


def _janela_principal(avaliacao: pd.DataFrame, quantil: float) -> pd.DataFrame:
    """Retém a região principal para visualização, sem alterar os dados do modelo."""
    if not 0.5 <= quantil < 1:
        raise ValueError("quantil deve estar entre 0.5 e 1 (limite superior exclusivo)")
    observed_limit = avaliacao["alvo"].quantile(quantil)
    predicted_limit = avaliacao["previsto_continuo"].quantile(quantil)
    return avaliacao.loc[
        avaliacao["alvo"].le(observed_limit)
        & avaliacao["previsto_continuo"].le(predicted_limit)
    ].copy()


def grafico_observado_previsto(
    avaliacao: pd.DataFrame, destino: Path, quantil: float = 0.98
) -> None:
    """Salva observado × previsto focado na região principal dos dados."""
    plt = _pyplot()
    principal = _janela_principal(avaliacao, quantil)
    observed = principal["alvo"].to_numpy(dtype=float)
    predicted = principal["previsto_continuo"].to_numpy(dtype=float)
    maximum = max(observed.max(initial=0), predicted.max(initial=0), 1)
    figure, axis = plt.subplots(figsize=(10, 7))
    labels = list(pd.unique(principal["previsto_faixa"]))
    colors = {label: BLOCK_COLORS[index % len(BLOCK_COLORS)] for index, label in enumerate(labels)}
    for block in labels:
        selected = principal["previsto_faixa"].eq(block).fillna(False).to_numpy(dtype=bool)
        axis.scatter(
            observed[selected], predicted[selected], s=38, alpha=.75,
            color=colors[block], label=f"{block} ({selected.sum()})",
            edgecolors="#222222", linewidths=.35,
        )
    axis.plot([0, maximum], [0, maximum], color="black", label="Linha de 45°")
    if len(observed) > 1 and not np.isclose(observed, observed[0]).all():
        slope, intercept = np.polyfit(observed, predicted, 1)
        axis.plot(
            [0, maximum], [intercept, slope * maximum + intercept],
            "--", color="#e31a1c", label="Regressão linear",
        )
    axis.set(
        xlim=(0, maximum * 1.05), ylim=(0, maximum * 1.05),
        xlabel="Volume observado", ylabel="Volume previsto",
        title=f"Regressão: volume observado × previsto (região principal, p{quantil:.0%})",
    )
    hidden = len(avaliacao) - len(principal)
    axis.text(
        .99, .01, f"{hidden} outliers ocultos",
        transform=axis.transAxes, ha="right", va="bottom", fontsize=9,
        bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none"},
    )
    axis.grid(alpha=.3)
    axis.legend(title="Grupos K-Means")
    figure.tight_layout()
    figure.savefig(destino, dpi=150)
    plt.close(figure)


def gerar_graficos_regressao(
    avaliacao: pd.DataFrame, pasta: str | Path, quantil: float = 0.98
) -> list[Path]:
    """Gera gráficos de regressão com os blocos de classificação sobrepostos."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    paths = [pasta / "observado_vs_previsto.png", pasta / "clusters_pca.png"]
    grafico_observado_previsto(avaliacao, paths[0], quantil)
    grafico_clusters_pca(avaliacao, paths[1], quantil)
    return paths


def grafico_clusters_pca(
    avaliacao: pd.DataFrame, destino: Path, quantil: float = 0.98
) -> None:
    """Mostra os clusters no espaço dos dois componentes principais."""
    plt = _pyplot()
    principal = _janela_principal(avaliacao, quantil)
    labels = list(pd.unique(principal["previsto_faixa"]))
    colors = {label: BLOCK_COLORS[index % len(BLOCK_COLORS)] for index, label in enumerate(labels)}
    figure, axis = plt.subplots(figsize=(10, 7))
    for label in labels:
        selected = principal["previsto_faixa"].eq(label).fillna(False).to_numpy(dtype=bool)
        axis.scatter(
            principal.loc[selected, "componente_pca_1"],
            principal.loc[selected, "componente_pca_2"],
            color=colors[label], alpha=.65, s=35, label=label,
        )
        centroid = principal.loc[selected, ["centroide_pca_1", "centroide_pca_2"]].iloc[0]
        axis.scatter(
            centroid["centroide_pca_1"], centroid["centroide_pca_2"],
            color=colors[label], edgecolors="black", marker="X", s=180,
        )
    axis.set(
        xlabel="Componente principal 1", ylabel="Componente principal 2",
        title=f"Clusters K-Means após PCA (região principal, p{quantil:.0%})",
    )
    axis.grid(alpha=.3)
    axis.legend(title="Clusters")
    figure.tight_layout()
    figure.savefig(destino, dpi=150)
    plt.close(figure)


# Compatibilidade com chamadas antigas ao módulo.
gerar_graficos_classificacao = gerar_graficos_regressao
