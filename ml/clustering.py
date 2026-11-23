"""Clusterização das unidades de saúde por perfil epidemiológico e operacional.

Unidade de análise: **uma linha por unidade de saúde notificadora (CNES)** com
pelo menos ``MIN_NOTIFICACOES_UNIDADE`` notificações no período. Cada unidade é
descrita por indicadores agregados; nenhum paciente e nenhum caso individual é
agrupado ou classificado. Só as variáveis ativas (``CLUSTER_FEATURES``) entram
na distância; as ilustrativas (``CLUSTER_FEATURES_ILUSTRATIVAS``) aparecem
apenas no perfil de cada cluster.

Etapas:
1. construção do perfil das unidades (``construir_perfil_unidades``);
2. imputação pela mediana + padronização z-score (``StandardScaler``);
3. redução de dimensionalidade com PCA, mantendo o menor número de componentes
   que explica ``PCA_VARIANCIA_MINIMA`` da variância;
4. K-Means (k escolhido pela silhueta), HDBSCAN (parâmetros escolhidos pela
   silhueta com limite de ruído) e DBSCAN (eps pela curva k-distância);
5. comparação dos algoritmos e perfil de cada cluster.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd

if __package__:
    from .config import (
        CLUSTER_FEATURES, CLUSTER_FEATURES_ILUSTRATIVAS, DBSCAN_MIN_SAMPLES,
        ESTABILIDADE_FRACAO, ESTABILIDADE_REAMOSTRAGENS, HDBSCAN_MIN_CLUSTER_SIZE,
        HDBSCAN_MIN_SAMPLES, K_RANGE, MIN_NOTIFICACOES_UNIDADE, PCA_VARIANCIA_MINIMA,
        RANDOM_STATE, RUIDO_MAXIMO,
    )
    from .data import UNIDADE_NAO_INFORMADA
else:
    from config import (
        CLUSTER_FEATURES, CLUSTER_FEATURES_ILUSTRATIVAS, DBSCAN_MIN_SAMPLES,
        ESTABILIDADE_FRACAO, ESTABILIDADE_REAMOSTRAGENS, HDBSCAN_MIN_CLUSTER_SIZE,
        HDBSCAN_MIN_SAMPLES, K_RANGE, MIN_NOTIFICACOES_UNIDADE, PCA_VARIANCIA_MINIMA,
        RANDOM_STATE, RUIDO_MAXIMO,
    )
    from data import UNIDADE_NAO_INFORMADA


COLUNAS_REGISTRO = [
    "unidade_saude", "doenca", "ano", "inicio_semana_notificacao", "bairro",
    "confirmado", "hospitalizado", "idade", "dias_sintoma_notificacao",
    "tempo_encerramento", "mun_notificacao",
]

VARIAVEIS_EXCLUIDAS = {
    "caso_grave": "Apenas 14 casos graves em ~36 mil notificações: raro demais para diferenciar unidades.",
    "obito": "Apenas 7 óbitos: raro demais para diferenciar unidades.",
    "prop_dengue": "Complemento de chikungunya + zika (correlação de -0,94 com chikungunya).",
    "sinais_alarme": "Informado em menos de 1/3 dos registros e concentrado em poucas unidades.",
}

TODAS_FEATURES = list(CLUSTER_FEATURES) + list(CLUSTER_FEATURES_ILUSTRATIVAS)

# Nome interpretativo do cluster a partir da variável ativa mais marcante.
ROTULOS_VARIAVEL = {
    ("log_notificacoes_semana", 1): "Alto volume",
    ("log_notificacoes_semana", -1): "Baixo volume",
    ("prop_chikungunya", 1): "Mais chikungunya",
    ("prop_chikungunya", -1): "Predomínio de dengue",
    ("taxa_hospitalizacao", 1): "Perfil hospitalar",
    ("taxa_hospitalizacao", -1): "Perfil ambulatorial",
    ("idade_media", 1): "Pacientes mais velhos",
    ("idade_media", -1): "Perfil pediátrico",
    ("dispersao_territorial", 1): "Abrangência ampla",
    ("dispersao_territorial", -1): "Abrangência local",
    ("crescimento_24_25", 1): "Notificação recente (2024–25)",
    ("crescimento_24_25", -1): "Notificação em queda",
}
NOME_RUIDO = "Atípicas (ruído)"

BAIRRO_NAO_INFORMADO = "Não informado"
ROTULO_RUIDO = -1
ANO_CORTE_CRESCIMENTO = 2024


# ---------------------------------------------------------------------------
# 1. Perfil das unidades
# ---------------------------------------------------------------------------

def _booleano(serie: pd.Series) -> pd.Series:
    """Converte True/False (texto ou booleano) em 1.0/0.0, mantendo ausentes."""
    return serie.astype("string").str.strip().str.lower().map({"true": 1.0, "false": 0.0}).astype(float)


def _entropia_normalizada(bairros: pd.Series, total_bairros: int) -> float:
    """Entropia de Shannon dos bairros, dividida pelo máximo atingível."""
    validos = bairros[bairros.notna() & bairros.ne(BAIRRO_NAO_INFORMADO)]
    if len(validos) < 2:
        return np.nan
    p = validos.value_counts(normalize=True).to_numpy()
    maximo = np.log(min(len(validos), total_bairros))
    return float(-(p * np.log(p)).sum() / maximo) if maximo > 0 else 0.0


def _cv_semanal(semanas: pd.Series) -> float:
    """CV das notificações semanais entre a primeira e a última semana ativa."""
    contagem = semanas.value_counts()
    indice = pd.date_range(semanas.min(), semanas.max(), freq="7D")
    contagem = contagem.reindex(indice, fill_value=0)
    media = contagem.mean()
    return float(contagem.std(ddof=0) / media) if media > 0 else np.nan


def _moda(serie: pd.Series, ignorar: Iterable[str] = ()) -> Any:
    validos = serie[serie.notna() & ~serie.isin(list(ignorar))]
    return validos.mode().iloc[0] if not validos.empty else pd.NA


def preparar_registros(registros: pd.DataFrame, anos: Iterable[int] | None = None) -> pd.DataFrame:
    """Converte tipos e aplica o filtro de anos e de unidade informada."""
    frame = registros.copy()
    frame["semana"] = pd.to_datetime(frame["inicio_semana_notificacao"], errors="coerce")
    frame["ano"] = pd.to_numeric(frame["ano"], errors="coerce")
    frame = frame.dropna(subset=["semana", "ano"])
    frame["ano"] = frame["ano"].astype(int)
    if anos:
        frame = frame[frame["ano"].isin(list(anos))]
    frame = frame[frame["unidade_saude"].ne(UNIDADE_NAO_INFORMADA)]
    frame["bairro"] = frame["bairro"].astype("string").fillna(BAIRRO_NAO_INFORMADO)
    for coluna in ("confirmado", "hospitalizado"):
        frame[coluna] = _booleano(frame[coluna])
    for coluna in ("idade", "dias_sintoma_notificacao", "tempo_encerramento"):
        frame[coluna] = pd.to_numeric(frame[coluna], errors="coerce")
    if frame.empty:
        raise ValueError("Nenhum registro válido para o período selecionado")
    return frame


def construir_perfil_unidades(
    registros: pd.DataFrame, min_notificacoes: int = MIN_NOTIFICACOES_UNIDADE
) -> pd.DataFrame:
    """Uma linha por unidade de saúde com as variáveis de ``CLUSTER_FEATURES``.

    ``registros`` deve vir de ``preparar_registros``. Unidades com menos de
    ``min_notificacoes`` notificações são descartadas: indicadores calculados
    sobre poucos registros (ex.: uma taxa de 1/3) são instáveis.
    """
    contagem = registros["unidade_saude"].value_counts()
    selecionadas = contagem[contagem >= min_notificacoes].index
    if len(selecionadas) < 4:
        raise ValueError("Menos de 4 unidades com notificações suficientes para agrupar")
    frame = registros[registros["unidade_saude"].isin(selecionadas)]
    semanas_periodo = max(1, (registros["semana"].max() - registros["semana"].min()).days // 7 + 1)
    total_bairros = registros.loc[registros["bairro"].ne(BAIRRO_NAO_INFORMADO), "bairro"].nunique()

    linhas = []
    for unidade, grupo in frame.groupby("unidade_saude", sort=True):
        n = len(grupo)
        recentes = int((grupo["ano"] >= ANO_CORTE_CRESCIMENTO).sum())
        linhas.append({
            "unidade_saude": unidade,
            "log_notificacoes_semana": float(np.log1p(n / semanas_periodo)),
            "prop_chikungunya": float(grupo["doenca"].eq("Chikungunya").mean()),
            "prop_zika": float(grupo["doenca"].eq("Zika").mean()),
            "taxa_confirmacao": float(grupo["confirmado"].mean()),
            "taxa_hospitalizacao": float(grupo["hospitalizado"].mean()),
            "completude_registro": float(grupo["hospitalizado"].notna().mean()),
            "idade_media": float(grupo["idade"].mean()),
            "crescimento_24_25": float(np.log((recentes + 1) / (n - recentes + 1))),
            "cv_semanal": _cv_semanal(grupo["semana"]),
            "dispersao_territorial": _entropia_normalizada(grupo["bairro"], total_bairros),
            "atraso_notificacao_mediano": float(grupo["dias_sintoma_notificacao"].median()),
            "tempo_encerramento_mediano": float(grupo["tempo_encerramento"].median()),
            # Colunas descritivas (não entram no modelo).
            "n_notificacoes": n,
            "doenca_predominante": _moda(grupo["doenca"]),
            "bairro_principal": _moda(grupo["bairro"], [BAIRRO_NAO_INFORMADO]),
            "municipio_notificacao": _moda(grupo["mun_notificacao"].astype("string")),
            "primeiro_ano": int(grupo["ano"].min()),
            "ultimo_ano": int(grupo["ano"].max()),
        })
    return pd.DataFrame(linhas).set_index("unidade_saude")


# ---------------------------------------------------------------------------
# 2–3. Pré-processamento e redução de dimensionalidade
# ---------------------------------------------------------------------------

def criar_preprocessador(escalonador: Any | None = None):
    """Imputação pela mediana seguida de padronização (z-score por padrão)."""
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return Pipeline([
        ("imputacao", SimpleImputer(strategy="median")),
        ("escalonamento", escalonador if escalonador is not None else StandardScaler()),
    ])


def reduzir_dimensionalidade(
    padronizado: np.ndarray, variancia_minima: float = PCA_VARIANCIA_MINIMA
) -> tuple[Any, int, np.ndarray]:
    """Ajusta PCA completo e retém componentes até ``variancia_minima``."""
    from sklearn.decomposition import PCA

    pca = PCA(random_state=RANDOM_STATE).fit(padronizado)
    acumulada = np.cumsum(pca.explained_variance_ratio_)
    n_componentes = int(np.searchsorted(acumulada, variancia_minima) + 1)
    n_componentes = max(2, min(n_componentes, len(acumulada)))
    return pca, n_componentes, pca.transform(padronizado)[:, :n_componentes]


# ---------------------------------------------------------------------------
# 4. Algoritmos
# ---------------------------------------------------------------------------

def metricas_particao(espaco: np.ndarray, rotulos: np.ndarray) -> dict[str, Any]:
    """Silhueta, Davies-Bouldin e Calinski-Harabasz ignorando pontos de ruído."""
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

    rotulos = np.asarray(rotulos)
    validos = rotulos != ROTULO_RUIDO
    n_clusters = len(set(rotulos[validos]))
    resultado: dict[str, Any] = {
        "n_clusters": n_clusters,
        "n_ruido": int((~validos).sum()),
        "ruido_pct": float((~validos).mean() * 100),
        "silhueta": None,
        "davies_bouldin": None,
        "calinski_harabasz": None,
    }
    if 2 <= n_clusters < validos.sum():
        x, y = espaco[validos], rotulos[validos]
        resultado.update(
            silhueta=float(silhouette_score(x, y)),
            davies_bouldin=float(davies_bouldin_score(x, y)),
            calinski_harabasz=float(calinski_harabasz_score(x, y)),
        )
    return resultado


def _renumerar_por_tamanho(rotulos: np.ndarray) -> np.ndarray:
    """Clusters numerados a partir de 1, do maior para o menor; ruído fica -1."""
    rotulos = np.asarray(rotulos)
    validos = pd.Series(rotulos[rotulos != ROTULO_RUIDO])
    ordem = validos.value_counts().sort_index().sort_values(ascending=False, kind="stable").index
    mapa = {int(antigo): novo for novo, antigo in enumerate(ordem, start=1)}
    return np.array([mapa.get(int(r), ROTULO_RUIDO) for r in rotulos])


def estabilidade_kmeans(
    espaco: np.ndarray, k: int, rotulos: np.ndarray,
    reamostragens: int = ESTABILIDADE_REAMOSTRAGENS, fracao: float = ESTABILIDADE_FRACAO,
) -> float:
    """ARI médio entre a partição completa e partições de subamostras."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score

    gerador = np.random.default_rng(RANDOM_STATE)
    tamanho = int(len(espaco) * fracao)
    valores = []
    for _ in range(reamostragens):
        indices = gerador.choice(len(espaco), tamanho, replace=False)
        semente = int(gerador.integers(1_000_000))
        parcial = KMeans(n_clusters=k, n_init=10, random_state=semente).fit_predict(espaco[indices])
        valores.append(adjusted_rand_score(rotulos[indices], parcial))
    return float(np.mean(valores))


def avaliar_kmeans(espaco: np.ndarray, k_range: Iterable[int] = K_RANGE) -> dict[str, Any]:
    """Avalia k por inércia (cotovelo), silhueta, Davies-Bouldin, Calinski-Harabasz e estabilidade."""
    from sklearn.cluster import KMeans

    por_k: dict[int, dict[str, Any]] = {}
    for k in k_range:
        if k >= len(espaco):
            continue
        modelo = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(espaco)
        por_k[k] = {
            "inercia": float(modelo.inertia_),
            **metricas_particao(espaco, modelo.labels_),
            "estabilidade_ari": estabilidade_kmeans(espaco, k, modelo.labels_),
            "tamanhos": sorted(np.bincount(modelo.labels_).tolist(), reverse=True),
        }
    if not por_k:
        raise ValueError("Dados insuficientes para avaliar o K-Means")
    melhor_k = max(por_k, key=lambda k: por_k[k]["silhueta"] or -1)
    return {"por_k": por_k, "k_selecionado": melhor_k,
            "criterio": "maior coeficiente de silhueta; cotovelo e estabilidade "
                        f"(ARI médio em {ESTABILIDADE_REAMOSTRAGENS} subamostras de "
                        f"{ESTABILIDADE_FRACAO:.0%}) exibidos como apoio"}


def treinar_kmeans(espaco: np.ndarray, k: int) -> tuple[Any, np.ndarray]:
    from sklearn.cluster import KMeans

    modelo = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(espaco)
    return modelo, _renumerar_por_tamanho(modelo.labels_)


def _selecionar(grade: list[dict[str, Any]], ruido_maximo: float) -> dict[str, Any] | None:
    elegiveis = [
        item for item in grade
        if item["silhueta"] is not None and item["ruido_pct"] <= ruido_maximo * 100
    ]
    if not elegiveis:
        return None
    return max(elegiveis, key=lambda item: (round(item["silhueta"], 6), -item["ruido_pct"]))


def avaliar_hdbscan(
    espaco: np.ndarray,
    min_cluster_sizes: Iterable[int] = HDBSCAN_MIN_CLUSTER_SIZE,
    min_samples_values: Iterable[int | None] = HDBSCAN_MIN_SAMPLES,
    ruido_maximo: float = RUIDO_MAXIMO,
) -> dict[str, Any]:
    """Busca em grade do HDBSCAN; escolhe a maior silhueta com ruído limitado."""
    from sklearn.cluster import HDBSCAN

    grade = []
    for min_cluster_size in min_cluster_sizes:
        for min_samples in min_samples_values:
            rotulos = HDBSCAN(
                min_cluster_size=min_cluster_size, min_samples=min_samples, copy=True
            ).fit_predict(espaco)
            grade.append({
                "min_cluster_size": min_cluster_size,
                "min_samples": min_samples,
                **metricas_particao(espaco, rotulos),
            })
    return {
        "grade": grade,
        "selecionado": _selecionar(grade, ruido_maximo),
        "criterio": f"maior silhueta (sem ruído) entre configurações com ≥2 clusters "
                    f"e ruído ≤ {ruido_maximo:.0%}",
    }


def treinar_hdbscan(espaco: np.ndarray, min_cluster_size: int, min_samples: int | None):
    from sklearn.cluster import HDBSCAN

    modelo = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, copy=True)
    rotulos = modelo.fit_predict(espaco)
    return modelo, _renumerar_por_tamanho(rotulos)


def distancias_k_vizinho(espaco: np.ndarray, k: int = DBSCAN_MIN_SAMPLES) -> np.ndarray:
    """Distância de cada ponto ao seu k-ésimo vizinho, em ordem crescente."""
    from sklearn.neighbors import NearestNeighbors

    # O próprio ponto é o vizinho 0, por isso k + 1 vizinhos.
    distancias, _ = NearestNeighbors(n_neighbors=k + 1).fit(espaco).kneighbors(espaco)
    return np.sort(distancias[:, -1])


def _joelho(curva: np.ndarray) -> float:
    """Ponto da curva mais distante da reta que liga o primeiro ao último ponto."""
    x = np.linspace(0, 1, len(curva))
    y = (curva - curva.min()) / max(np.ptp(curva), 1e-12)
    distancia = np.abs(y - x)
    return float(curva[int(np.argmax(distancia))])


def avaliar_dbscan(
    espaco: np.ndarray, min_samples: int = DBSCAN_MIN_SAMPLES, ruido_maximo: float = RUIDO_MAXIMO
) -> dict[str, Any]:
    """DBSCAN com eps candidatos tirados da curva k-distância."""
    from sklearn.cluster import DBSCAN

    curva = distancias_k_vizinho(espaco, min_samples)
    joelho = _joelho(curva)
    candidatos = sorted({round(float(v), 4) for v in
                         [joelho, *np.percentile(curva, [50, 60, 70, 80, 90, 95])]})
    grade = []
    for eps in candidatos:
        rotulos = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(espaco)
        grade.append({"eps": eps, **metricas_particao(espaco, rotulos)})
    return {
        "min_samples": min_samples,
        "eps_joelho": joelho,
        "grade": grade,
        "selecionado": _selecionar(grade, ruido_maximo),
        "criterio": f"eps entre o joelho e percentis da curva k-distância; maior silhueta "
                    f"com ≥2 clusters e ruído ≤ {ruido_maximo:.0%}",
    }


# ---------------------------------------------------------------------------
# 5. Interpretação
# ---------------------------------------------------------------------------

def zscores_unidades(perfil: pd.DataFrame) -> pd.DataFrame:
    """z-score de todas as variáveis (ativas e ilustrativas) após imputar a mediana."""
    valores = perfil[TODAS_FEATURES].astype(float)
    valores = valores.fillna(valores.median())
    desvio = valores.std(ddof=0).replace(0, 1)
    return (valores - valores.mean()) / desvio


def perfil_clusters(
    perfil: pd.DataFrame, zscores: pd.DataFrame, rotulos: np.ndarray, coluna: str
) -> list[dict[str, Any]]:
    """Médias originais, z-score médio e descrição das variáveis ativas mais marcantes."""
    resultado = []
    for cluster in sorted(set(rotulos), key=lambda c: (c == ROTULO_RUIDO, c)):
        selecao = rotulos == cluster
        z = zscores[selecao].mean()
        destaque = z[list(CLUSTER_FEATURES)].abs().sort_values(ascending=False).head(3).index
        principal = destaque[0]
        rotulo = ROTULOS_VARIAVEL[(principal, 1 if z[principal] > 0 else -1)]
        resultado.append({
            coluna: int(cluster),
            "nome": NOME_RUIDO if cluster == ROTULO_RUIDO else f"Cluster {cluster} · {rotulo}",
            "n_unidades": int(selecao.sum()),
            "n_notificacoes": int(perfil.loc[selecao, "n_notificacoes"].sum()),
            "unidades": list(perfil.index[selecao]),
            "medias": {f: _json(perfil.loc[selecao, f].mean()) for f in TODAS_FEATURES},
            "zscores": {f: _json(z[f]) for f in TODAS_FEATURES},
            "descricao": ", ".join(f"{'↑' if z[f] > 0 else '↓'} {f}" for f in destaque),
        })
    return resultado


def _json(valor: Any) -> Any:
    """Converte números numpy/NaN para tipos aceitos pelo JSON."""
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (float, np.floating)):
        return None if np.isnan(valor) else float(valor)
    return valor


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------

@dataclass
class ResultadoClusterizacao:
    perfil: pd.DataFrame          # variáveis, rótulos e coordenadas por unidade
    relatorio: dict[str, Any]     # tudo o que vai para o JSON
    padronizado: np.ndarray       # variáveis após imputação + z-score
    componentes: np.ndarray       # espaço PCA retido (onde os algoritmos rodam)
    pca: Any
    k_distancias: np.ndarray
    silhueta_amostras: np.ndarray
    zscores: pd.DataFrame         # z-score de todas as variáveis (para os perfis)


def sensibilidade_escalonamento(perfil: pd.DataFrame, k: int) -> dict[str, Any]:
    """Compara a silhueta do K-Means com diferentes escalonadores."""
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

    resultado = {}
    for nome, escalonador in [("StandardScaler (adotado)", StandardScaler()),
                              ("RobustScaler", RobustScaler()),
                              ("MinMaxScaler", MinMaxScaler())]:
        x = criar_preprocessador(escalonador).fit_transform(perfil[list(CLUSTER_FEATURES)])
        _, n_comp, comp = reduzir_dimensionalidade(x)
        _, rotulos = treinar_kmeans(comp, k)
        resultado[nome] = {"n_componentes_pca": n_comp,
                           "silhueta": float(silhouette_score(comp, rotulos))}
    return resultado


def comparar_conjuntos_variaveis(perfil: pd.DataFrame) -> dict[str, Any]:
    """Mesmo pipeline com as variáveis ativas × com todas as 12 variáveis."""
    resultado = {}
    for nome, colunas in [("ativas (adotado)", list(CLUSTER_FEATURES)), ("todas", TODAS_FEATURES)]:
        x = criar_preprocessador().fit_transform(perfil[colunas])
        pca, n_comp, comp = reduzir_dimensionalidade(x)
        kmeans = avaliar_kmeans(comp)
        k = kmeans["k_selecionado"]
        hdbscan = avaliar_hdbscan(comp, ruido_maximo=1.0)
        com_clusters = [g for g in hdbscan["grade"] if g["n_clusters"] >= 2]
        resultado[nome] = {
            "n_variaveis": len(colunas),
            "n_componentes_pca": n_comp,
            "variancia_retida": float(np.sum(pca.explained_variance_ratio_[:n_comp])),
            "k_selecionado": k,
            "silhueta_kmeans": kmeans["por_k"][k]["silhueta"],
            "estabilidade_kmeans": kmeans["por_k"][k]["estabilidade_ari"],
            "hdbscan_menor_ruido_pct": min((g["ruido_pct"] for g in com_clusters), default=None),
        }
    return resultado


def comparar_espacos(padronizado: np.ndarray, componentes: np.ndarray, k: int) -> dict[str, Any]:
    """K-Means no espaço padronizado completo × no espaço PCA retido."""
    from sklearn.metrics import adjusted_rand_score, silhouette_score

    _, rotulos_completo = treinar_kmeans(padronizado, k)
    _, rotulos_pca = treinar_kmeans(componentes, k)
    return {
        "silhueta_espaco_completo": float(silhouette_score(padronizado, rotulos_completo)),
        "silhueta_espaco_pca": float(silhouette_score(componentes, rotulos_pca)),
        "ari_entre_particoes": float(adjusted_rand_score(rotulos_completo, rotulos_pca)),
        "nota": "A silhueta tende a ser maior em menos dimensões; o ARI mostra se a "
                "partição encontrada no espaço PCA é a mesma do espaço completo.",
    }


def executar_clusterizacao(
    registros_brutos: pd.DataFrame,
    min_notificacoes: int = MIN_NOTIFICACOES_UNIDADE,
    anos: Iterable[int] | None = None,
) -> ResultadoClusterizacao:
    from sklearn.manifold import TSNE
    from sklearn.metrics import adjusted_rand_score, silhouette_samples

    registros = preparar_registros(registros_brutos, anos)
    perfil = construir_perfil_unidades(registros, min_notificacoes)
    features = list(CLUSTER_FEATURES)

    preprocessador = criar_preprocessador()
    padronizado = preprocessador.fit_transform(perfil[features])
    pca, n_componentes, componentes = reduzir_dimensionalidade(padronizado)

    avaliacao_kmeans = avaliar_kmeans(componentes)
    k = avaliacao_kmeans["k_selecionado"]
    _, rotulos_kmeans = treinar_kmeans(componentes, k)

    avaliacao_hdbscan = avaliar_hdbscan(componentes)
    escolha = avaliacao_hdbscan["selecionado"]
    if escolha is None:
        raise ValueError("Nenhuma configuração do HDBSCAN atendeu aos critérios")
    modelo_hdbscan, rotulos_hdbscan = treinar_hdbscan(
        componentes, escolha["min_cluster_size"], escolha["min_samples"]
    )

    avaliacao_dbscan = avaliar_dbscan(componentes)
    k_distancias = distancias_k_vizinho(componentes, avaliacao_dbscan["min_samples"])

    perplexidade = float(min(15, (len(perfil) - 1) / 3))
    tsne = TSNE(n_components=2, perplexity=perplexidade, init="pca",
                random_state=RANDOM_STATE).fit_transform(padronizado)

    perfil = perfil.assign(
        cluster_kmeans=rotulos_kmeans,
        cluster_hdbscan=rotulos_hdbscan,
        prob_hdbscan=np.round(modelo_hdbscan.probabilities_, 4),
        pc1=componentes[:, 0], pc2=componentes[:, 1],
        tsne_1=tsne[:, 0], tsne_2=tsne[:, 1],
    )

    escalonador = preprocessador.named_steps["escalonamento"]
    imputador = preprocessador.named_steps["imputacao"]
    validos_hdb = rotulos_hdbscan != ROTULO_RUIDO
    comparacao = [
        {"algoritmo": "K-Means", "parametros": f"k={k}",
         **metricas_particao(componentes, rotulos_kmeans)},
        {"algoritmo": "HDBSCAN",
         "parametros": f"min_cluster_size={escolha['min_cluster_size']}, "
                       f"min_samples={escolha['min_samples']}",
         **metricas_particao(componentes, rotulos_hdbscan)},
    ]
    if avaliacao_dbscan["selecionado"]:
        comparacao.append({"algoritmo": "DBSCAN",
                           "parametros": f"eps={avaliacao_dbscan['selecionado']['eps']}, "
                                         f"min_samples={avaliacao_dbscan['min_samples']}",
                           **{c: v for c, v in avaliacao_dbscan["selecionado"].items() if c != "eps"}})
    else:
        comparacao.append({"algoritmo": "DBSCAN", "parametros": "nenhum eps atendeu aos critérios",
                           "n_clusters": None, "n_ruido": None, "ruido_pct": None, "silhueta": None,
                           "davies_bouldin": None, "calinski_harabasz": None})

    total_notificacoes = len(registros)
    zscores = zscores_unidades(perfil)
    perfis = {
        "kmeans": perfil_clusters(perfil, zscores, rotulos_kmeans, "cluster_kmeans"),
        "hdbscan": perfil_clusters(perfil, zscores, rotulos_hdbscan, "cluster_hdbscan"),
    }
    nomes = {alg: {c[f"cluster_{alg}"]: c["nome"] for c in perfis[alg]} for alg in perfis}
    perfil = perfil.assign(
        nome_cluster_kmeans=perfil["cluster_kmeans"].map(nomes["kmeans"]),
        nome_cluster_hdbscan=perfil["cluster_hdbscan"].map(nomes["hdbscan"]),
    )
    relatorio = {
        "unidade_analise": "Unidade de saúde notificadora (código CNES); uma linha por unidade.",
        "o_que_nao_e_agrupado": "Pacientes e casos individuais não são agrupados nem classificados.",
        "periodo": {
            "anos": sorted(int(a) for a in registros["ano"].unique()),
            "inicio": str(registros["semana"].min().date()),
            "fim": str(registros["semana"].max().date()),
        },
        "min_notificacoes": min_notificacoes,
        "n_unidades_total": int(registros["unidade_saude"].nunique()),
        "n_unidades_agrupadas": int(len(perfil)),
        "notificacoes_cobertas_pct": float(perfil["n_notificacoes"].sum() / total_notificacoes * 100),
        "variaveis": CLUSTER_FEATURES,
        "variaveis_ilustrativas": CLUSTER_FEATURES_ILUSTRATIVAS,
        "variaveis_excluidas": VARIAVEIS_EXCLUIDAS,
        "selecao_variaveis": comparar_conjuntos_variaveis(perfil),
        "preprocessamento": {
            "imputacao": "mediana (SimpleImputer)",
            "valores_imputados": {f: int(perfil[f].isna().sum()) for f in features},
            "escalonamento": "StandardScaler (z-score): (x - média) / desvio-padrão",
            "justificativa": "K-Means, HDBSCAN e DBSCAN usam distância euclidiana; sem padronizar, "
                             "variáveis de escala maior (idade em anos, log do volume) dominariam "
                             "as proporções (0–1).",
            "media": {f: _json(v) for f, v in zip(features, escalonador.mean_)},
            "desvio_padrao": {f: _json(v) for f, v in zip(features, escalonador.scale_)},
            "mediana_imputacao": {f: _json(v) for f, v in zip(features, imputador.statistics_)},
            "sensibilidade_escalonamento": sensibilidade_escalonamento(perfil, k),
        },
        "pca": {
            "criterio": f"menor número de componentes com variância acumulada ≥ {PCA_VARIANCIA_MINIMA:.0%}",
            "n_componentes": n_componentes,
            "n_variaveis_originais": len(features),
            "variancia_retida": float(np.sum(pca.explained_variance_ratio_[:n_componentes])),
            "variancia_por_componente": [float(v) for v in pca.explained_variance_ratio_],
            "variancia_acumulada": [float(v) for v in np.cumsum(pca.explained_variance_ratio_)],
            "cargas": {
                f"PC{i + 1}": {f: float(v) for f, v in zip(features, pca.components_[i])}
                for i in range(n_componentes)
            },
            "comparacao_espacos": comparar_espacos(padronizado, componentes, k),
            "visualizacao": f"t-SNE 2D (perplexidade {perplexidade:.1f}) apenas para visualização.",
        },
        "kmeans": {**avaliacao_kmeans,
                   "por_k": {str(c): v for c, v in avaliacao_kmeans["por_k"].items()}},
        "hdbscan": avaliacao_hdbscan,
        "dbscan": avaliacao_dbscan,
        "comparacao": comparacao,
        "ari_kmeans_hdbscan": float(adjusted_rand_score(
            rotulos_kmeans[validos_hdb], rotulos_hdbscan[validos_hdb]
        )) if validos_hdb.sum() > 1 else None,
        "perfis": perfis,
    }
    return ResultadoClusterizacao(
        perfil=perfil, relatorio=relatorio, padronizado=padronizado,
        componentes=componentes, pca=pca, k_distancias=k_distancias,
        silhueta_amostras=silhouette_samples(componentes, rotulos_kmeans), zscores=zscores,
    )
