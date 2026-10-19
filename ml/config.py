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

# Intervalos de contagem que preservam a resolução dos volumes baixos, onde
# está concentrada a maior parte dos grupos semana × unidade × agravo.
RANDOM_STATE = 42
PCA_COMPONENTS = 2
K_RANGE = range(2, 9)
