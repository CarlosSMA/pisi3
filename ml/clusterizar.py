"""Executa a clusterização das unidades de saúde e salva tabelas, métricas e gráficos.

Uso:
    python ml/clusterizar.py [--dados PASTA] [--saida PASTA] [--min-notificacoes N] [--anos 2023 2024 2025]
"""

import argparse
import json
from pathlib import Path

if __package__:
    from .clustering import COLUNAS_REGISTRO, executar_clusterizacao
    from .clustering_plots import gerar_graficos_clusterizacao
    from .config import MIN_NOTIFICACOES_UNIDADE
    from .data import carregar_registros_tratados
else:
    # Permite executar `python clusterizar.py` a partir desta pasta.
    from clustering import COLUNAS_REGISTRO, executar_clusterizacao
    from clustering_plots import gerar_graficos_clusterizacao
    from config import MIN_NOTIFICACOES_UNIDADE
    from data import carregar_registros_tratados


RAIZ = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = RAIZ / "data" / "dados_tratados"


def main() -> None:
    parser = argparse.ArgumentParser(description="Agrupa unidades de saúde por perfil epidemiológico.")
    parser.add_argument("--dados", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--saida", type=Path, default=Path("resultados_clusterizacao"),
                        help="Pasta onde serão salvos CSVs, JSON e gráficos.")
    parser.add_argument("--min-notificacoes", type=int, default=MIN_NOTIFICACOES_UNIDADE,
                        help="Mínimo de notificações para uma unidade ser agrupada.")
    parser.add_argument("--anos", type=int, nargs="+", default=None,
                        help="Anos considerados (padrão: todos os anos presentes nos dados).")
    args = parser.parse_args()

    registros = carregar_registros_tratados(args.dados, COLUNAS_REGISTRO)
    resultado = executar_clusterizacao(registros, args.min_notificacoes, args.anos)

    args.saida.mkdir(parents=True, exist_ok=True)
    resultado.perfil.round(4).to_csv(args.saida / "perfil_unidades.csv", sep=";")
    relatorio = resultado.relatorio
    (args.saida / "metricas_clusterizacao.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    caminhos = gerar_graficos_clusterizacao(resultado, args.saida / "graficos")

    resumo = {
        "unidades_agrupadas": relatorio["n_unidades_agrupadas"],
        "unidades_total": relatorio["n_unidades_total"],
        "pca": f"{relatorio['pca']['n_componentes']} componentes, "
               f"{relatorio['pca']['variancia_retida']:.1%} da variância",
        "clusters_kmeans": {p["nome"]: p["n_unidades"] for p in relatorio["perfis"]["kmeans"]},
        "graficos": [str(c) for c in caminhos],
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
