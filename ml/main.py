import argparse
import json
from pathlib import Path

if __package__:
    from .data import carregar_tabela_tratada
    from .features import adicionar_baselines, criar_features
    from .model import treinar_sistema
else:
    # Permite executar `python main.py` a partir desta pasta.
    from data import carregar_tabela_tratada
    from features import adicionar_baselines, criar_features
    from model import treinar_sistema


DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dados_tratados"


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina previsão agregada de carga epidemiológica.")
    parser.add_argument("--dados", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--saida", type=Path, default=Path("previsoes_carga.csv"))
    parser.add_argument("--metricas", type=Path, default=Path("metricas_carga.json"))
    parser.add_argument("--horizonte", type=int, default=1)
    parser.add_argument(
        "--graficos",
        type=Path,
        default=Path("graficos_classificacao"),
        help="Pasta onde serão salvos os gráficos da regressão e dos blocos.",
    )
    parser.add_argument(
        "--quantil-graficos",
        type=float,
        default=0.98,
        help="Quantil máximo exibido nos gráficos (padrão: 0.98).",
    )
    args = parser.parse_args()
    tabela = carregar_tabela_tratada(args.dados)
    features = adicionar_baselines(criar_features(tabela, args.horizonte))
    sistema = treinar_sistema(tabela, args.horizonte)
    if __package__:
        from .plots import gerar_graficos_regressao
    else:
        from plots import gerar_graficos_regressao
    gerar_graficos_regressao(sistema.classification_test, args.graficos, args.quantil_graficos)
    latest = features["inicio_semana"].max()
    previsoes = sistema.prever(features[features["inicio_semana"] == latest])
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    previsoes.to_csv(args.saida, sep=";", index=False)
    args.metricas.parent.mkdir(parents=True, exist_ok=True)
    args.metricas.write_text(json.dumps(sistema.metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(sistema.metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
