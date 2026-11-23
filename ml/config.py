GROUP_COLUMNS = ["inicio_semana", "unidade_saude", "doenca"]

FEATURE_COLUMNS = [
    "unidade_saude", "doenca", "ano", "semana", "mes",
    "lag_1", "lag_2", "lag_4", "lag_8",
    "media_4", "media_8", "tendencia_4",
]

BASELINE_COLUMNS = [
    "baseline_media_movel",
    "baseline_semana_anterior",
    "baseline_anual",
    "baseline_media_historica",
]

RANDOM_STATE = 42

# Faixas de volume da previsão: limiares dados pelos quantis das semanas de
# treino com pelo menos uma notificação (≈79% das semanas têm zero, então
# quantis sobre todas as semanas colapsariam em zero).
FAIXAS_VOLUME = ["baixo", "moderado", "alto", "muito alto"]
QUANTIS_FAIXA_VOLUME = (0.50, 0.75, 0.90)

# --- Clusterização das unidades de saúde -----------------------------------
# Unidade de análise: uma linha por unidade de saúde notificadora (CNES).
MIN_NOTIFICACOES_UNIDADE = 30

# Variáveis ATIVAS: entram no cálculo de distância. Cada uma representa uma
# dimensão distinta do perfil da unidade (volume, agravo, gravidade, faixa
# etária, território e tendência) e são pouco correlacionadas entre si.
CLUSTER_FEATURES = {
    "log_notificacoes_semana": "Volume: log(1 + notificações por semana do período)",
    "prop_chikungunya": "Proporção das notificações que são de chikungunya",
    "taxa_hospitalizacao": "Proporção de hospitalizados (entre registros com o campo informado)",
    "idade_media": "Idade média dos pacientes notificados (anos)",
    "dispersao_territorial": "Entropia normalizada dos bairros de residência (0 = um bairro, 1 = uniforme)",
    "crescimento_24_25": "log((notificações 2024–25 + 1) / (notificações 2022–23 + 1))",
}

# Variáveis ILUSTRATIVAS: calculadas e exibidas no perfil de cada cluster, mas
# fora da distância. Descrevem o processo de notificação/registro (e não o
# perfil da unidade) ou são redundantes/ruidosas. A comparação entre usar só
# as ativas e usar as 12 variáveis fica em "selecao_variaveis" no relatório.
CLUSTER_FEATURES_ILUSTRATIVAS = {
    "taxa_confirmacao": "Proporção de casos confirmados (depende do acesso a exames)",
    "completude_registro": "Proporção de registros com hospitalização informada (qualidade da coleta)",
    "atraso_notificacao_mediano": "Mediana de dias entre início dos sintomas e notificação",
    "tempo_encerramento_mediano": "Mediana de dias entre notificação e encerramento",
    "cv_semanal": "Coeficiente de variação das notificações semanais (r = -0,55 com o volume)",
    "prop_zika": "Proporção das notificações que são de zika (mediana de 1%)",
}

# Redução de dimensionalidade: menor número de componentes que explica pelo
# menos esta fração da variância das variáveis padronizadas.
PCA_VARIANCIA_MINIMA = 0.80

K_RANGE = range(2, 11)
# Estabilidade do K-Means: reamostragens de 80% das unidades, comparadas à
# partição completa pelo índice de Rand ajustado (ARI).
ESTABILIDADE_REAMOSTRAGENS = 30
ESTABILIDADE_FRACAO = 0.8
HDBSCAN_MIN_CLUSTER_SIZE = (3, 4, 5, 6, 8)
HDBSCAN_MIN_SAMPLES = (1, 2, 3, None)
DBSCAN_MIN_SAMPLES = 4
RUIDO_MAXIMO = 0.25
