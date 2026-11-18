"""Gráficos de regressão e blocos de volume previstos."""

from pathlib import Path
import re
from typing import Any, Mapping

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


def _labels_por_media(labels: pd.Series) -> list[str]:
    """Ordena os rótulos pela média informada no nome de cada grupo."""
    unique_labels = list(pd.unique(labels))

    def media_do_label(label: str) -> tuple[float, int]:
        match = re.search(r"Média:\s*(-?\d+(?:[.,]\d+)?)", str(label))
        media = float(match.group(1).replace(",", ".")) if match else float("inf")
        match_grupo = re.search(r"Grupo\s+(\d+)", str(label))
        grupo = int(match_grupo.group(1)) if match_grupo else 0
        return media, grupo

    return sorted(unique_labels, key=media_do_label)


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
    labels = _labels_por_media(principal["previsto_faixa"])
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
    avaliacao: pd.DataFrame,
    pasta: str | Path,
    quantil: float = 0.98,
    cluster_report: Mapping[str, Any] | None = None,
) -> list[Path]:
    """Gera gráficos de regressão com os blocos de classificação sobrepostos."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    paths = [
        pasta / "observado_vs_previsto.png",
        pasta / "clusters_pca.png",
    ]
    grafico_observado_previsto(avaliacao, paths[0], quantil)
    grafico_clusters_pca(avaliacao, paths[1], quantil)
    if cluster_report:
        paths.extend([
            pasta / "cotovelo_kmeans.png",
            pasta / "silhueta_kmeans.png",
        ])
        grafico_cotovelo_kmeans(cluster_report, paths[2])
        grafico_silhueta_kmeans(cluster_report, paths[3])
    return paths


def grafico_clusters_pca(
    avaliacao: pd.DataFrame, destino: Path, quantil: float = 0.98
) -> None:
    """Mostra os clusters no espaço dos dois componentes principais."""
    plt = _pyplot()
    principal = _janela_principal(avaliacao, quantil)
    labels = _labels_por_media(principal["previsto_faixa"])
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


def _valores_por_k(report: Mapping[str, Any], chave: str) -> tuple[list[int], list[float]]:
    """Converte os dados do relatório de K-Means em listas ordenadas por k."""
    valores = report.get(chave, {})
    if not isinstance(valores, Mapping):
        return [], []
    pares = sorted(
        (int(k), float(valor))
        for k, valor in valores.items()
        if valor is not None
    )
    return [k for k, _ in pares], [valor for _, valor in pares]


def grafico_cotovelo_kmeans(
    cluster_report: Mapping[str, Any], destino: Path
) -> None:
    """Salva o método do cotovelo com a quantidade escolhida destacada."""
    plt = _pyplot()
    k_values, inertia = _valores_por_k(cluster_report, "inercia_elbow")
    if not k_values:
        raise ValueError("Relatório não contém os dados de inércia do cotovelo")

    figure, axis = plt.subplots(figsize=(10, 7))
    axis.plot(k_values, inertia, marker="o", linewidth=2, color="#2c7fb8")
    selected_k = cluster_report.get("k_selecionado")
    if selected_k is not None:
        selected_k = int(selected_k)
        if selected_k in k_values:
            index = k_values.index(selected_k)
            axis.axvline(
                selected_k, color="#d7191c", linestyle="--",
                label=f"k selecionado = {selected_k}",
            )
            axis.scatter(
                [selected_k], [inertia[index]], s=130,
                color="#d7191c", edgecolors="black", zorder=4,
            )
    axis.set(
        xlabel="Quantidade de clusters (k)",
        ylabel="Inércia",
        title="Método do cotovelo para seleção de k no K-Means",
        xticks=k_values,
    )
    axis.grid(alpha=.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(destino, dpi=150)
    plt.close(figure)


def grafico_silhueta_kmeans(
    cluster_report: Mapping[str, Any], destino: Path
) -> None:
    """Salva a silhueta por k com os coeficientes no eixo horizontal."""
    plt = _pyplot()
    k_values, silhouette = _valores_por_k(cluster_report, "silhueta_por_k")
    if not k_values:
        raise ValueError("Relatório não contém os dados de silhueta")

    figure, axis = plt.subplots(figsize=(10, 7))
    colors = ["#bdbdbd" if k <= 2 else "#41ab5d" for k in k_values]
    axis.barh(k_values, silhouette, color=colors, edgecolor="#333333", height=.65)
    selected_k = cluster_report.get("k_selecionado")
    if selected_k is not None:
        selected_k = int(selected_k)
        if selected_k in k_values:
            index = k_values.index(selected_k)
            axis.scatter(
                [silhouette[index]], [selected_k], s=130,
                color="#d7191c", edgecolors="black", zorder=4,
                label=f"k selecionado = {selected_k}",
            )
            axis.axvline(
                silhouette[index], color="#d7191c", linestyle="--",
                linewidth=1, label=f"silhueta selecionada = {silhouette[index]:.3f}",
            )
    axis.set(
        xlabel="Coeficiente de silhueta",
        ylabel="Quantidade de clusters (k)",
        title="Silhueta por k no K-Means (k > 2 são elegíveis)",
        yticks=k_values,
    )
    axis.grid(axis="x", alpha=.3)
    axis.axvline(0, color="#333333", linewidth=.8)
    axis.legend()
    figure.tight_layout()
    figure.savefig(destino, dpi=150)
    plt.close(figure)


# Compatibilidade com chamadas antigas ao módulo.
gerar_graficos_classificacao = gerar_graficos_regressao
