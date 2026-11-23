"""Gráfico de regressão com a faixa de volume prevista sobreposta.

Os gráficos da clusterização das unidades de saúde ficam em
``clustering_plots.py``.
"""

from pathlib import Path

import numpy as np
import pandas as pd

if __package__:
    from .config import FAIXAS_VOLUME
else:
    from config import FAIXAS_VOLUME

# Sequência ordinal de um único matiz (azul): faixa mais alta = mais escura.
FAIXA_CORES = dict(zip(FAIXAS_VOLUME, ["#9ec5f4", "#5598e7", "#256abf", "#0d366b"]))


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _janela_principal(avaliacao: pd.DataFrame, quantil: float) -> pd.DataFrame:
    """Retém a região principal para visualização, sem alterar os dados do modelo."""
    if not 0.5 <= quantil < 1:
        raise ValueError("quantil deve estar entre 0.5 e 1 (limite superior exclusivo)")
    observed_limit = avaliacao["alvo"].quantile(quantil)
    predicted_limit = avaliacao["previsto_continuo"].quantile(quantil)
    return avaliacao.loc[
        avaliacao["alvo"].le(observed_limit)
        & avaliacao["previsto_continuo"].le(predicted_limit)
    ].copy()


def grafico_observado_previsto(
    avaliacao: pd.DataFrame, destino: Path, quantil: float = 0.98
) -> None:
    """Salva observado × previsto focado na região principal dos dados."""
    plt = _pyplot()
    principal = _janela_principal(avaliacao, quantil)
    observed = principal["alvo"].to_numpy(dtype=float)
    predicted = principal["previsto_continuo"].to_numpy(dtype=float)
    maximum = max(observed.max(initial=0), predicted.max(initial=0), 1)
    figure, axis = plt.subplots(figsize=(10, 7))
    for faixa in FAIXAS_VOLUME:
        selected = principal["previsto_faixa"].eq(faixa).fillna(False).to_numpy(dtype=bool)
        if not selected.any():
            continue
        axis.scatter(
            observed[selected], predicted[selected], s=38, alpha=.75,
            color=FAIXA_CORES[faixa], label=f"{faixa} ({selected.sum()})",
            edgecolors="#222222", linewidths=.35,
        )
    axis.plot([0, maximum], [0, maximum], color="black", label="Linha de 45°")
    if len(observed) > 1 and not np.isclose(observed, observed[0]).all():
        slope, intercept = np.polyfit(observed, predicted, 1)
        axis.plot(
            [0, maximum], [intercept, slope * maximum + intercept],
            "--", color="#e34948", label="Regressão linear",
        )
    axis.set(
        xlim=(0, maximum * 1.05), ylim=(0, maximum * 1.05),
        xlabel="Volume observado", ylabel="Volume previsto",
        title=f"Regressão: volume observado × previsto (região principal, p{quantil:.0%})",
    )
    hidden = len(avaliacao) - len(principal)
    axis.text(
        .99, .01, f"{hidden} outliers ocultos",
        transform=axis.transAxes, ha="right", va="bottom", fontsize=9,
        bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none"},
    )
    axis.grid(alpha=.3)
    axis.legend(title="Faixa de volume prevista")
    figure.tight_layout()
    figure.savefig(destino, dpi=150)
    plt.close(figure)


def gerar_graficos_regressao(
    avaliacao: pd.DataFrame,
    pasta: str | Path,
    quantil: float = 0.98,
) -> list[Path]:
    """Gera o gráfico de regressão com as faixas de volume sobrepostas."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "observado_vs_previsto.png"
    grafico_observado_previsto(avaliacao, destino, quantil)
    return [destino]


# Compatibilidade com chamadas antigas ao módulo.
gerar_graficos_classificacao = gerar_graficos_regressao
