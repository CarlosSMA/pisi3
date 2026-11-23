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

# Paleta categórica em ordem fixa (nunca reciclada). Acima de três cores num
# mesmo gráfico de dispersão algumas se confundem (laranja × rosa, e mais ainda
# para daltônicos); por isso cada cluster também tem um marcador próprio e
# rótulo direto, e a cor nunca é a única pista.
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARCADORES = ["o", "s", "^", "D", "P", "v", "X", "*"]
CINZA = "#bdbcb5"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

# Nomes legíveis das variáveis ativas, usados para descrever os eixos da PCA.
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


def _juntar(nomes: list[str]) -> str:
    """["a", "b", "c"] → "a, b e c"."""
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + " e " + nomes[-1]


def _rotulo_componente(
    resultado: ResultadoClusterizacao, indice: int, sentido: str,
    quebrar: bool = False, maximo: int = 3, carga_minima: float = .3,
) -> str:
    """Descreve um eixo da PCA pelas variáveis de maior carga no componente.

    Cargas positivas aumentam no sentido do eixo; negativas diminuem. Ex.:
    "PC1 (26% da variância) — para a direita: mais hospitalização e %
    chikungunya, menos volume de notificações".
    """
    pca = resultado.relatorio["pca"]
    cargas = pca["cargas"][f"PC{indice + 1}"]
    principais = sorted(cargas.items(), key=lambda item: abs(item[1]), reverse=True)[:maximo]
    principais = [(variavel, carga) for variavel, carga in principais if abs(carga) >= carga_minima]
    mais = [NOMES_VARIAVEIS.get(v, v) for v, carga in principais if carga > 0]
    menos = [NOMES_VARIAVEIS.get(v, v) for v, carga in principais if carga < 0]
    partes = ([f"mais {_juntar(mais)}"] if mais else []) + ([f"menos {_juntar(menos)}"] if menos else [])
    cabecalho = f"PC{indice + 1} ({pca['variancia_por_componente'][indice]:.0%} da variância)"
    if quebrar:
        return f"{cabecalho}\n{sentido}: " + ",\n".join(partes)
    return f"{cabecalho} — {sentido}: " + ", ".join(partes)


def _eixos_pca(eixo, resultado: ResultadoClusterizacao) -> None:
    eixo.set_xlabel(_rotulo_componente(resultado, 0, "para a direita"))
    eixo.set_ylabel(_rotulo_componente(resultado, 1, "para cima", quebrar=True))


# ---------------------------------------------------------------------------

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


def _pequenos_multiplos(x, y, rotulos, nomes, titulo, rotulo_x, rotulo_y, destino):
    """Um painel por cluster: o cluster em destaque, as demais unidades em cinza."""
    plt = _pyplot()
    clusters = sorted(set(rotulos))
    colunas = min(3, len(clusters))
    linhas = int(np.ceil(len(clusters) / colunas))
    figura, eixos = plt.subplots(linhas, colunas, figsize=(5 * colunas, 4.3 * linhas),
                                 sharex=True, sharey=True, squeeze=False)
    for posicao, eixo in enumerate(eixos.flat):
        if posicao >= len(clusters):
            eixo.set_visible(False)
            continue
        cluster = clusters[posicao]
        selecao = rotulos == cluster
        eixo.scatter(x[~selecao], y[~selecao], s=28, color=CINZA, alpha=.6, linewidths=0)
        eixo.scatter(x[selecao], y[selecao], s=60, color=CORES[posicao % len(CORES)],
                     edgecolors=SUPERFICIE, linewidths=1.5)
        eixo.scatter([x[selecao].mean()], [y[selecao].mean()], s=180, marker="X",
                     color=CORES[posicao % len(CORES)], edgecolors=TINTA, linewidths=1.2)
        eixo.set_title(f"{nomes[cluster]} ({selecao.sum()} unid.)", fontsize=10)
        eixo.grid(True)
    for eixo in eixos[-1]:
        eixo.set_xlabel(rotulo_x)
    for eixo in eixos[:, 0]:
        eixo.set_ylabel(rotulo_y)
    figura.suptitle(titulo, x=.01, ha="left", fontweight="bold", fontsize=13)
    return _salvar(figura, destino)


def grafico_kmeans_pca(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    """Todos os clusters do K-Means num único plano PC1 × PC2."""
    plt = _pyplot()
    perfil = resultado.perfil
    n = resultado.relatorio["pca"]["n_componentes"]
    figura, eixo = plt.subplots(figsize=(12, 7.5))
    for posicao, cluster in enumerate(sorted(perfil["cluster_kmeans"].unique())):
        dados = perfil[perfil["cluster_kmeans"].eq(cluster)]
        nome = dados["nome_cluster_kmeans"].iloc[0]
        cor, marcador = CORES[posicao % len(CORES)], MARCADORES[posicao % len(MARCADORES)]
        eixo.scatter(dados["pc1"], dados["pc2"], s=70, marker=marcador, color=cor,
                     edgecolors=SUPERFICIE, linewidths=1.2, zorder=3, label=f"{nome} ({len(dados)} unid.)")
        centro_x, centro_y = dados["pc1"].mean(), dados["pc2"].mean()
        eixo.scatter([centro_x], [centro_y], s=320, marker=marcador, color=cor,
                     edgecolors=TINTA, linewidths=1.8, zorder=4)
        eixo.annotate(f"Cluster {cluster}", xy=(centro_x, centro_y), xytext=(12, 10),
                      textcoords="offset points", fontsize=10, fontweight="bold", color=TINTA, zorder=5,
                      bbox={"boxstyle": "round,pad=0.25", "facecolor": SUPERFICIE, "edgecolor": GRADE,
                            "alpha": .7})
    _eixos_pca(eixo, resultado)
    eixo.set_title("Clusters do K-Means nos dois primeiros componentes da PCA")
    eixo.text(0, 1.01, f"Marcador grande com contorno = centróide do cluster. O agrupamento usa os {n} "
                       "componentes retidos;\naqui aparecem só os dois primeiros, por isso alguns clusters "
                       "se sobrepõem.", transform=eixo.transAxes, fontsize=9, color=TINTA_SECUNDARIA,
              va="bottom")
    eixo.set_title(eixo.get_title(loc="left"), loc="left", pad=34)
    eixo.grid(True)
    eixo.legend(title="Cluster (K-Means)", loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    return _salvar(figura, destino)


def grafico_hdbscan_pca(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    perfil = resultado.perfil
    selecionado = resultado.relatorio["hdbscan"]["selecionado"]
    figura, eixo = plt.subplots(figsize=(12, 7.5))
    ruido = perfil["cluster_hdbscan"].eq(ROTULO_RUIDO)
    eixo.scatter(perfil.loc[ruido, "pc1"], perfil.loc[ruido, "pc2"], s=60, marker="x",
                 color=TINTA_SECUNDARIA, label=f"Atípicas / ruído ({ruido.sum()})")
    for posicao, cluster in enumerate(sorted(perfil.loc[~ruido, "cluster_hdbscan"].unique())):
        selecao = perfil["cluster_hdbscan"].eq(cluster)
        nome = perfil.loc[selecao, "nome_cluster_hdbscan"].iloc[0]
        eixo.scatter(perfil.loc[selecao, "pc1"], perfil.loc[selecao, "pc2"],
                     s=30 + 70 * perfil.loc[selecao, "prob_hdbscan"], color=CORES[posicao],
                     edgecolors=SUPERFICIE, linewidths=1.5, label=f"{nome} ({selecao.sum()})")
    n = resultado.relatorio["pca"]["n_componentes"]
    _eixos_pca(eixo, resultado)
    eixo.set_title(f"HDBSCAN (min_cluster_size={selecionado['min_cluster_size']}, "
                   f"min_samples={selecionado['min_samples']})")
    eixo.text(0, 1.01, f"Tamanho do ponto = probabilidade de pertencer ao cluster. O agrupamento usa os "
                       f"{n} componentes retidos;\nunidades atípicas no meio da nuvem se afastam nos "
                       f"componentes não exibidos.", transform=eixo.transAxes, fontsize=9,
              color=TINTA_SECUNDARIA, va="bottom")
    eixo.set_title(eixo.get_title(loc="left"), loc="left", pad=34)
    eixo.grid(True)
    eixo.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    return _salvar(figura, destino)


def grafico_k_distancia(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    plt = _pyplot()
    dbscan = resultado.relatorio["dbscan"]
    curva = resultado.k_distancias
    figura, eixo = plt.subplots(figsize=(10, 6))
    eixo.plot(np.arange(1, len(curva) + 1), curva, color=CORES[0])
    eixo.axhline(dbscan["eps_joelho"], color=TINTA_SECUNDARIA, linestyle="--", linewidth=1)
    eixo.text(1, dbscan["eps_joelho"], f" joelho: eps ≈ {dbscan['eps_joelho']:.2f}",
              va="bottom", color=TINTA)
    resumo = "\n".join(
        f"eps {g['eps']:.3f}: {g['n_clusters']} cluster(s), {g['ruido_pct']:.0f}% ruído"
        for g in dbscan["grade"]
    )
    eixo.text(.02, .97, resumo, transform=eixo.transAxes, va="top", fontsize=8.5, color=TINTA_SECUNDARIA,
              bbox={"facecolor": SUPERFICIE, "edgecolor": GRADE})
    eixo.set(xlabel="Unidades ordenadas", ylabel=f"Distância ao {dbscan['min_samples']}º vizinho",
             title="DBSCAN: curva k-distância" + (
                 " — nenhum eps separou as unidades com ruído aceitável"
                 if dbscan["selecionado"] is None else f" — eps escolhido = {dbscan['selecionado']['eps']:.2f}"
             ))
    eixo.grid(axis="y")
    return _salvar(figura, destino)


def grafico_tsne(resultado: ResultadoClusterizacao, destino: Path) -> Path:
    perfil = resultado.perfil
    nomes = dict(zip(perfil["cluster_kmeans"], perfil["nome_cluster_kmeans"]))
    return _pequenos_multiplos(
        perfil["tsne_1"].to_numpy(), perfil["tsne_2"].to_numpy(), perfil["cluster_kmeans"].to_numpy(),
        nomes, "t-SNE 2D (apenas visualização; distâncias não são preservadas) — clusters do K-Means",
        "t-SNE 1", "t-SNE 2", destino,
    )


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
