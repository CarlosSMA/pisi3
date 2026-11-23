"""Gráficos da clusterização das unidades de saúde.

Os arquivos são numerados na ordem da
análise: variáveis → K-Means → perfis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

if __package__:
    from .clustering import TODAS_FEATURES, ResultadoClusterizacao
    from .config import CLUSTER_FEATURES
else:
    from clustering import TODAS_FEATURES, ResultadoClusterizacao
    from config import CLUSTER_FEATURES

# Paleta categórica em ordem fixa (nunca reciclada). Em gráficos de dispersão
# com mais de três grupos usamos pequenos múltiplos (um painel por cluster).
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CINZA = "#bdbcb5"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
DIVERGENTE = ["#184f95", "#3987e5", "#9ec5f4", "#f0efec", "#f4a9a8", "#e34948", "#9e2b2a"]


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "font.family": "sans-serif", "font.size": 10,
        "text.color": TINTA, "axes.labelcolor": TINTA_SECUNDARIA, "axes.titlecolor": TINTA,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.edgecolor": EIXO, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": TINTA_SECUNDARIA, "ytick.color": TINTA_SECUNDARIA,
        "grid.color": GRADE, "grid.linewidth": .8, "legend.frameon": False, "axes.axisbelow": True,
        "lines.linewidth": 2,
    })
    return plt


def _salvar(figura, destino: Path) -> Path:
    figura.tight_layout()
    figura.savefig(destino, dpi=150)
    import matplotlib.pyplot as plt

    plt.close(figura)
    return destino


def _mapa_divergente():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("divergente", DIVERGENTE)


def _heatmap(eixo, valores: pd.DataFrame, limite: float, formato: str = "{:.2f}"):
    imagem = eixo.imshow(valores.to_numpy(dtype=float), cmap=_mapa_divergente(),
                         vmin=-limite, vmax=limite, aspect="auto")
    eixo.set_xticks(range(valores.shape[1]), valores.columns, rotation=40, ha="right")
    eixo.set_yticks(range(valores.shape[0]), valores.index)
    eixo.tick_params(length=0)
    for spine in eixo.spines.values():
        spine.set_visible(False)
    for (i, j), valor in np.ndenumerate(valores.to_numpy(dtype=float)):
        if np.isnan(valor):
            continue
        cor = "#ffffff" if abs(valor) > limite * .6 else TINTA
        eixo.text(j, i, formato.format(valor), ha="center", va="center", fontsize=8, color=cor)
    return imagem


def _separador_ativas(eixo, vertical: bool = True) -> None:
    """Linha entre as variáveis ativas e as ilustrativas."""
    posicao = len(CLUSTER_FEATURES) - .5
    (eixo.axvline if vertical else eixo.axhline)(posicao, color=TINTA, linewidth=1.5)


# ---------------------------------------------------------------------------

def grafico_correlacao(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    correlacao = resultado.perfil[TODAS_FEATURES].corr()
    figura, eixo = plt.subplots(figsize=(11, 9))
    imagem = _heatmap(eixo, correlacao, 1.0)
    _separador_ativas(eixo, vertical=True)
    _separador_ativas(eixo, vertical=False)
    figura.colorbar(imagem, ax=eixo, shrink=.7, label="Correlação de Pearson")
    eixo.set_title("Correlação entre as variáveis por unidade de saúde\n"
                   "(acima/à esquerda da linha: ativas; abaixo/à direita: ilustrativas)")
    return _salvar(figura, destino)


def grafico_cotovelo(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    por_k = resultado.relatorio["kmeans"]["por_k"]
    ks = [int(k) for k in por_k]
    inercia = [por_k[str(k)]["inercia"] for k in ks]
    escolhido = resultado.relatorio["kmeans"]["k_selecionado"]
    figura, eixo = plt.subplots(figsize=(10, 6))
    eixo.plot(ks, inercia, marker="o", color=CORES[0], markersize=7)
    eixo.scatter([escolhido], [por_k[str(escolhido)]["inercia"]], s=160, color=CORES[0],
                 edgecolors=TINTA, linewidths=1.5, zorder=4)
    eixo.annotate(f"k escolhido = {escolhido}", xy=(escolhido, por_k[str(escolhido)]["inercia"]),
                  xytext=(12, 12), textcoords="offset points", color=TINTA)
    eixo.set(xticks=ks, xlabel="Número de clusters (k)", ylabel="Inércia (soma das distâncias² ao centróide)",
             title="Método do cotovelo")
    eixo.grid(axis="y")
    return _salvar(figura, destino)


def grafico_silhueta_por_k(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    por_k = resultado.relatorio["kmeans"]["por_k"]
    ks = [int(k) for k in por_k]
    silhueta = [por_k[str(k)]["silhueta"] for k in ks]
    estabilidade = [por_k[str(k)]["estabilidade_ari"] for k in ks]
    escolhido = resultado.relatorio["kmeans"]["k_selecionado"]
    figura, eixo = plt.subplots(figsize=(10, 6))
    eixo.plot(ks, silhueta, marker="o", color=CORES[0], markersize=7, label="Silhueta (critério)")
    eixo.plot(ks, estabilidade, marker="s", color=CORES[1], markersize=7,
              label="Estabilidade (ARI em subamostras)")
    eixo.axvline(escolhido, color=TINTA_SECUNDARIA, linestyle="--", linewidth=1)
    i = ks.index(escolhido)
    eixo.annotate(f"k = {escolhido}\nsilhueta {silhueta[i]:.2f}\nestabilidade {estabilidade[i]:.2f}",
                  xy=(escolhido, silhueta[i]), xytext=(10, -50), textcoords="offset points", color=TINTA)
    eixo.text(ks[-1], silhueta[-1], "  silhueta", va="center", color=TINTA_SECUNDARIA)
    eixo.text(ks[-1], estabilidade[-1], "  estabilidade", va="center", color=TINTA_SECUNDARIA)
    eixo.set(xticks=ks, xlim=(ks[0] - .3, ks[-1] + 1.3), ylim=(0, 1),
             xlabel="Número de clusters (k)", ylabel="Índice (0 a 1)",
             title="Escolha de k: maior silhueta, conferida pela estabilidade")
    eixo.grid(axis="y")
    eixo.legend(loc="upper left")
    return _salvar(figura, destino)


def grafico_diagrama_silhueta(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    rotulos = resultado.perfil["cluster_kmeans"].to_numpy()
    nomes = dict(zip(resultado.perfil["cluster_kmeans"], resultado.perfil["nome_cluster_kmeans"]))
    valores = resultado.silhueta_amostras
    media = float(np.mean(valores))
    figura, eixo = plt.subplots(figsize=(10, 7))
    base = 0
    for posicao, cluster in enumerate(sorted(set(rotulos))):
        ordenados = np.sort(valores[rotulos == cluster])
        y = np.arange(base, base + len(ordenados))
        eixo.barh(y, ordenados, height=.85, color=CORES[posicao % len(CORES)])
        eixo.text(-0.02, base + len(ordenados) / 2, nomes[cluster], ha="right", va="center",
                  color=TINTA, fontsize=9)
        base += len(ordenados) + 2
    eixo.axvline(media, color=TINTA, linestyle="--", linewidth=1)
    eixo.text(media, base, f" média {media:.2f}", va="bottom", color=TINTA)
    eixo.axvline(0, color=EIXO, linewidth=1)
    eixo.set(yticks=[], xlabel="Coeficiente de silhueta de cada unidade",
             title=f"Diagrama de silhueta — K-Means com k = {len(set(rotulos))}")
    eixo.spines["left"].set_visible(False)
    eixo.set_xlim(min(-.25, valores.min() - .05), 1)
    eixo.grid(axis="x")
    figura.subplots_adjust(left=.32)
    return _salvar(figura, destino)


def grafico_perfil(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    perfis = resultado.relatorio["perfis"]["kmeans"]
    tabela = pd.DataFrame(
        {f"{p['nome']} ({p['n_unidades']})": p["zscores"] for p in perfis}
    ).T[TODAS_FEATURES].astype(float)
    limite = max(1.5, float(np.nanmax(np.abs(tabela.to_numpy()))))
    figura, eixo = plt.subplots(figsize=(13, 1.2 + .7 * len(tabela)))
    imagem = _heatmap(eixo, tabela, limite, "{:+.1f}")
    _separador_ativas(eixo, vertical=True)
    eixo.text(len(CLUSTER_FEATURES) / 2 - .5, -0.8, "variáveis ativas", ha="center", color=TINTA)
    eixo.text(len(CLUSTER_FEATURES) + len(TODAS_FEATURES[len(CLUSTER_FEATURES):]) / 2 - .5, -0.8,
              "variáveis ilustrativas", ha="center", color=TINTA_SECUNDARIA)
    figura.colorbar(imagem, ax=eixo, shrink=.9, label="z-score médio (0 = média das unidades)")
    eixo.set_title("Perfil de cada cluster do K-Means", pad=24)
    return _salvar(figura, destino)


def gerar_graficos_clusterizacao(resultado: ResultadoClusterizacao, pasta: str | Path) -> list[Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    funcoes: dict[str, Any] = {
        "01_correlacao_variaveis.png": grafico_correlacao,
        "04_kmeans_cotovelo.png": grafico_cotovelo,
        "05_kmeans_silhueta_por_k.png": grafico_silhueta_por_k,
        "06_kmeans_diagrama_silhueta.png": grafico_diagrama_silhueta,
        "11_perfil_clusters.png": grafico_perfil,
    }
    return [funcao(resultado, pasta / nome) for nome, funcao in funcoes.items()]
