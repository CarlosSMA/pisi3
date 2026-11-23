"""Gráficos da clusterização das unidades de saúde.

Os arquivos são numerados na ordem da
análise: K-Means → HDBSCAN/DBSCAN → visualização.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

if __package__:
    from .clustering import ROTULO_RUIDO, ResultadoClusterizacao
else:
    from clustering import ROTULO_RUIDO, ResultadoClusterizacao

# Paleta categórica em ordem fixa (nunca reciclada): cada cluster tem uma cor,
# identificada pela legenda.
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COR_RUIDO = "#a3a29c"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

# Nomes legíveis das variáveis ativas, usados para nomear os eixos da PCA.
NOMES_VARIAVEIS = {
    "log_notificacoes_semana": "volume de notificações",
    "prop_chikungunya": "% chikungunya",
    "taxa_hospitalizacao": "hospitalização",
    "idade_media": "idade média",
    "dispersao_territorial": "dispersão territorial",
    "crescimento_24_25": "crescimento 2024–25",
}


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "font.family": "sans-serif", "font.size": 10,
        "text.color": TINTA, "axes.labelcolor": TINTA_SECUNDARIA, "axes.titlecolor": TINTA,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 12, "axes.labelsize": 11,
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


def _nome_componente(resultado: ResultadoClusterizacao, indice: int) -> str:
    """Nome curto do eixo: variável de maior carga positiva × de maior carga negativa.

    A definição completa de cada componente fica no README.
    """
    cargas = resultado.relatorio["pca"]["cargas"][f"PC{indice + 1}"]
    positiva = max(cargas, key=cargas.get)
    negativa = min(cargas, key=cargas.get)
    nome = NOMES_VARIAVEIS.get(positiva, positiva)
    if cargas[negativa] < 0:
        nome += f" × {NOMES_VARIAVEIS.get(negativa, negativa)}"
    return f"Componente {indice + 1}: {nome}"


def _dispersao(resultado: ResultadoClusterizacao, algoritmo: str, x: str, y: str,
               titulo: str, rotulo_x: str, rotulo_y: str, destino: Path) -> Path:
    """Uma cor por cluster, todos no mesmo gráfico; ruído (se houver) em cinza."""
    plt = _pyplot()
    perfil = resultado.perfil
    rotulos = perfil[f"cluster_{algoritmo}"]
    nomes = perfil[f"nome_cluster_{algoritmo}"]
    figura, eixo = plt.subplots(figsize=(11, 7))
    clusters = sorted(c for c in rotulos.unique() if c != ROTULO_RUIDO)
    for posicao, cluster in enumerate(clusters):
        selecao = rotulos.eq(cluster)
        eixo.scatter(perfil.loc[selecao, x], perfil.loc[selecao, y], s=70, color=CORES[posicao % len(CORES)],
                     edgecolors=SUPERFICIE, linewidths=1, zorder=3,
                     label=f"{nomes[selecao].iloc[0]} ({selecao.sum()})")
    ruido = rotulos.eq(ROTULO_RUIDO)
    if ruido.any():
        eixo.scatter(perfil.loc[ruido, x], perfil.loc[ruido, y], s=70, color=COR_RUIDO,
                     edgecolors=SUPERFICIE, linewidths=1, zorder=2,
                     label=f"{nomes[ruido].iloc[0]} ({ruido.sum()})")
    eixo.set(title=titulo, xlabel=rotulo_x, ylabel=rotulo_y)
    eixo.grid(True)
    eixo.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    return _salvar(figura, destino)


# ---------------------------------------------------------------------------

def grafico_cotovelo(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    por_k = resultado.relatorio["kmeans"]["por_k"]
    ks = [int(k) for k in por_k]
    inercia = [por_k[str(k)]["inercia"] for k in ks]
    escolhido = resultado.relatorio["kmeans"]["k_selecionado"]
    figura, eixo = plt.subplots(figsize=(10, 6))
    eixo.plot(ks, inercia, marker="o", color=CORES[0], markersize=7)
    eixo.scatter([escolhido], [por_k[str(escolhido)]["inercia"]], s=150, color=CORES[0], zorder=4)
    eixo.annotate(f"k = {escolhido}", xy=(escolhido, por_k[str(escolhido)]["inercia"]),
                  xytext=(12, 12), textcoords="offset points", color=TINTA)
    eixo.set(xticks=ks, xlabel="Número de clusters (k)", ylabel="Inércia",
             title="Método do cotovelo (K-Means)")
    eixo.grid(axis="y")
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
    eixo.set(yticks=[], xlabel="Silhueta de cada unidade", title="Silhueta dos clusters (K-Means)")
    eixo.spines["left"].set_visible(False)
    eixo.set_xlim(min(-.25, valores.min() - .05), 1)
    eixo.grid(axis="x")
    figura.subplots_adjust(left=.32)
    return _salvar(figura, destino)


def grafico_kmeans_pca(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    return _dispersao(resultado, "kmeans", "pc1", "pc2", "Clusters do K-Means",
                      _nome_componente(resultado, 0), _nome_componente(resultado, 1), destino)


def grafico_hdbscan_pca(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    return _dispersao(resultado, "hdbscan", "pc1", "pc2", "Clusters do HDBSCAN",
                      _nome_componente(resultado, 0), _nome_componente(resultado, 1), destino)


def grafico_k_distancia(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    dbscan = resultado.relatorio["dbscan"]
    curva = resultado.k_distancias
    figura, eixo = plt.subplots(figsize=(10, 6))
    eixo.plot(np.arange(1, len(curva) + 1), curva, color=CORES[0])
    eixo.axhline(dbscan["eps_joelho"], color=TINTA_SECUNDARIA, linestyle="--", linewidth=1)
    eixo.text(1, dbscan["eps_joelho"], f" joelho: eps ≈ {dbscan['eps_joelho']:.2f}",
              va="bottom", color=TINTA)
    eixo.set(xlabel="Unidades (ordenadas pela distância)",
             ylabel=f"Distância ao {dbscan['min_samples']}º vizinho mais próximo",
             title="Curva k-distância (DBSCAN)")
    eixo.grid(axis="y")
    return _salvar(figura, destino)


def grafico_tsne(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    return _dispersao(resultado, "kmeans", "tsne_1", "tsne_2", "Clusters do K-Means (t-SNE)",
                      "Dimensão 1 do t-SNE", "Dimensão 2 do t-SNE", destino)


def gerar_graficos_clusterizacao(resultado: ResultadoClusterizacao, pasta: str | Path) -> list[Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    funcoes: dict[str, Any] = {
        "04_kmeans_cotovelo.png": grafico_cotovelo,
        "06_kmeans_diagrama_silhueta.png": grafico_diagrama_silhueta,
        "07_kmeans_clusters_pca.png": grafico_kmeans_pca,
        "08_hdbscan_clusters_pca.png": grafico_hdbscan_pca,
        "09_dbscan_k_distancia.png": grafico_k_distancia,
        "10_tsne_clusters.png": grafico_tsne,
    }
    return [funcao(resultado, pasta / nome) for nome, funcao in funcoes.items()]
