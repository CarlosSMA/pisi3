from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

if __package__:
    from .classification import rotular_clusters, treinar_classificador
    from .config import BASELINE_COLUMNS, FEATURE_COLUMNS, PCA_COMPONENTS, RANDOM_STATE
    from .features import adicionar_baselines, criar_features
    from .metrics import calcular_metricas
else:
    from classification import rotular_clusters, treinar_classificador
    from config import BASELINE_COLUMNS, FEATURE_COLUMNS, PCA_COMPONENTS, RANDOM_STATE
    from features import adicionar_baselines, criar_features
    from metrics import calcular_metricas


@dataclass
class SistemaPrevisao:
    regressor: Any
    classificador: Any
    preprocessor: Any
    scaler: Any
    cutoff: pd.Timestamp
    residual_quantile: float
    pca: Any
    pca_components: int
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
        # O grupo é atribuído pelo espaço reduzido do PCA e pelo K-Means.
        result["faixa_volume"] = rotular_clusters(
            self.classificador,
            self.pca.transform(self.scaler.transform(self.preprocessor.transform(x))),
        ).to_numpy()
        result["versao_modelo"] = "carga-semanal-v1"
        result["aviso"] = "Estimativa de apoio à gestão — não é decisão automática nem diagnóstico."
        return result


def treinar_sistema(tabela: pd.DataFrame, horizonte: int = 1, proporcao_teste: float = 0.2) -> SistemaPrevisao:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

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
    regressor = RandomForestRegressor(n_estimators=250, random_state=42, min_samples_leaf=2, n_jobs=-1)
    regressor.fit(x_train, train["alvo"])
    predicted = np.maximum(0, regressor.predict(x_test))
    residuals = np.abs(test["alvo"].to_numpy() - predicted)
    scaler = StandardScaler()
    pca = PCA(n_components=min(PCA_COMPONENTS, x_train.shape[1]), random_state=RANDOM_STATE)
    train_components = pca.fit_transform(scaler.fit_transform(x_train))
    test_components = pca.transform(scaler.transform(x_test))
    classificador, _, cluster_report = treinar_classificador(train_components, train["alvo"])
    test_cluster_ids = classificador.predict(test_components)
    centers = {
        classificador.cluster_labels_[cluster_id]: classificador.cluster_centers_[cluster_id]
        for cluster_id in range(classificador.n_clusters)
    }
    test_labels = rotular_clusters(classificador, test_components).to_numpy()
    metrics = {"regressao": calcular_metricas(test["alvo"], predicted)}
    metrics["baselines"] = {
        name: calcular_metricas(test["alvo"], test[name].fillna(train["alvo"].mean()))
        for name in BASELINE_COLUMNS
    }
    return SistemaPrevisao(
        regressor, classificador, preprocessor, scaler, cutoff,
        float(np.quantile(residuals, .9)) if len(residuals) else 0.0,
        pca, pca.n_components_, horizonte, metrics | {"clustering": cluster_report},
        test[["inicio_semana", "unidade_saude", "doenca", "alvo"]].assign(
            observado_faixa=test_labels,
            previsto_continuo=predicted,
            previsto_faixa=test_labels,
            componente_pca_1=test_components[:, 0],
            componente_pca_2=test_components[:, 1],
            centroide_pca_1=[centers[label][0] for label in test_labels],
            centroide_pca_2=[centers[label][1] for label in test_labels],
        ),
    )
