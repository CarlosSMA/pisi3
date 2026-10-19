import numpy as np
import pandas as pd


def calcular_metricas(y_true: pd.Series, predicted: pd.Series) -> dict[str, float]:
    error = np.asarray(y_true, dtype=float) - np.asarray(predicted, dtype=float)
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "erro_percentual": float(np.mean(np.abs(error) / np.maximum(np.asarray(y_true), 1)) * 100),
    }
