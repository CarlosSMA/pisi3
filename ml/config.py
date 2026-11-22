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
