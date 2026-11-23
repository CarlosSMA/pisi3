from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

if __package__:
    from .classification import avaliar_faixas, definir_limiares_faixa, rotular_faixa_volume
    from .config import BASELINE_COLUMNS, FEATURE_COLUMNS, RANDOM_STATE
    from .features import adicionar_baselines, criar_features
    from .metrics import calcular_metricas, calcular_metricas_justica
else:
    from classification import avaliar_faixas, definir_limiares_faixa, rotular_faixa_volume
    from config import BASELINE_COLUMNS, FEATURE_COLUMNS, RANDOM_STATE
    from features import adicionar_baselines, criar_features
    from metrics import calcular_metricas, calcular_metricas_justica


@dataclass
class SistemaPrevisao:
    regressor: Any
    preprocessor: Any
    cutoff: pd.Timestamp
    residual_quantile: float
    limiares_faixa: list[float]
    horizonte: int
    metrics: dict[str, Any]
    classification_test: pd.DataFrame

    def prever(self, features: pd.DataFrame) -> pd.DataFrame:
        x = features[FEATURE_COLUMNS]
        transformed = self.preprocessor.transform(x)
        prediction = np.maximum(0, self.regressor.predict(transformed))
        result = features[["periodo_alvo", "unidade_saude", "doenca"]].copy()
        result["estimativa"] = np.round(prediction, 2)
        result["limite_inferior"] = np.round(np.maximum(0, prediction - self.residual_quantile), 2)
        result["limite_superior"] = np.round(prediction + self.residual_quantile, 2)
        # Faixa definida por limiares históricos (quantis do treino).
        result["faixa_volume"] = rotular_faixa_volume(prediction, self.limiares_faixa).to_numpy()
        result["versao_modelo"] = "carga-semanal-v2"
        result["aviso"] = "Estimativa de apoio à gestão — não é decisão automática nem diagnóstico."
        return result


def treinar_sistema(tabela: pd.DataFrame, horizonte: int = 1, proporcao_teste: float = 0.2) -> SistemaPrevisao:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import OneHotEncoder

    data = adicionar_baselines(criar_features(tabela, horizonte)).dropna(
        subset=FEATURE_COLUMNS + ["alvo"]
    ).copy()
    if data.empty or data["inicio_semana"].nunique() < 3:
        raise ValueError("Dados insuficientes para validação temporal")
    dates = sorted(data["inicio_semana"].unique())
    cutoff = pd.Timestamp(dates[max(0, int(len(dates) * (1 - proporcao_teste)) - 1)])
    train, test = data[data["inicio_semana"] <= cutoff], data[data["inicio_semana"] > cutoff]
    if train.empty or test.empty:
        raise ValueError("A divisão temporal não produziu treino e teste")
    categorical = ["unidade_saude", "doenca"]
    numeric = [column for column in FEATURE_COLUMNS if column not in categorical]
    preprocessor = ColumnTransformer([
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
        ("numeric", "passthrough", numeric),
    ])
    x_train, x_test = preprocessor.fit_transform(train[FEATURE_COLUMNS]), preprocessor.transform(test[FEATURE_COLUMNS])
    regressor = RandomForestRegressor(n_estimators=250, random_state=RANDOM_STATE, min_samples_leaf=2, n_jobs=-1)
    regressor.fit(x_train, train["alvo"])
    predicted = np.maximum(0, regressor.predict(x_test))
    residuals = np.abs(test["alvo"].to_numpy() - predicted)

    limiares = definir_limiares_faixa(train["alvo"])
    observado_faixa = rotular_faixa_volume(test["alvo"], limiares).to_numpy()
    previsto_faixa = rotular_faixa_volume(predicted, limiares).to_numpy()

    metrics = {"regressao": calcular_metricas(test["alvo"], predicted)}
    metrics["baselines"] = {
        name: calcular_metricas(test["alvo"], test[name].fillna(train["alvo"].mean()))
        for name in BASELINE_COLUMNS
    }
    metrics["faixa_volume"] = {
        "criterio": "quantis 0,50/0,75/0,90 das semanas de treino com ≥1 notificação",
        "limiares": limiares,
        **avaliar_faixas(observado_faixa, previsto_faixa),
    }
    avaliacao_justica = test[["unidade_saude", "doenca", "alvo"]].assign(
        previsto_continuo=predicted
    )
    metrics["justica"] = {
        "unidade_saude": calcular_metricas_justica(
            avaliacao_justica, "unidade_saude"
        ),
        "doenca": calcular_metricas_justica(avaliacao_justica, "doenca"),
    }
    return SistemaPrevisao(
        regressor, preprocessor, cutoff,
        float(np.quantile(residuals, .9)) if len(residuals) else 0.0,
        limiares, horizonte, metrics,
        test[["inicio_semana", "unidade_saude", "doenca", "alvo"]].assign(
            observado_faixa=observado_faixa,
            previsto_continuo=predicted,
            previsto_faixa=previsto_faixa,
        ),
    )
