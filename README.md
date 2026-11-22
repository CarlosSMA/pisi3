<p align="center">
<img width="200" height="200" alt="logo-vetor-risco" src="https://github.com/user-attachments/assets/1df5a034-f71c-48be-b56c-8cc319672997" />
</p>

<h1 style="font-size: 3em; font-weight: bold;">🦟 VetorRisco</h1>

Este repositório contém a etapa de análise de dados e monitorização interativa do projeto VetorRisco.

A aplicação utiliza dados públicos de saúde epidemiológica do Recife sobre arboviroses (Dengue, Zika e Chikungunya), permitindo mapear a distribuição espacial, avaliar perfis demográficos, analisar a gravidade dos casos e acompanhar indicadores clínicos.

## 📊 Arquitetura dos Dashboards

***Geral (general_overview.py / dashboard.py):** Visão macro dos indicadores e volume de ocorrências.*

***Clínico (clinical_dashboard.py):** Análise dos sintomas, confirmações laboratoriais e diagnósticos.*

***Gravidade (severity_dashboard.py):** Monitorização de internações, evolução dos casos e níveis de risco.*

***Demográfico (demographic_dashboard.py):** Distribuição por faixa etária, género e perfil populacional.*

***Geoespacial (map_dashboard.py):** Mapeamento territorial e concentração dos casos na cidade do Recife.*

***Justiça operacional (fairness_dashboard.py):** Comparação do MAE, RMSE, erro percentual e viés do modelo entre unidades de saúde e agravos.*

## 📁 Modo de uso

**1. Clonar o repositório**

**2. Criar e ativar um ambiente virtual (Opcional, mas recomendado)**

python -m venv venv

**No Windows:**
venv\Scripts\activate

**No Linux/Mac:**
source venv/bin/activate

**3. Instalar as dependências**

pip install -r requirements.txt

**4. Executar a aplicação**

Para treinar o modelo e gerar as previsões, métricas e gráficos:

```bash
python ml/main.py
```

O script aceita as seguintes flags:

| Flag | Padrão | Descrição |
| --- | --- | --- |
| `--dados CAMINHO` | `data/dados_tratados` | Diretório com os dados tratados. |
| `--saida CAMINHO` | `previsoes_carga.csv` | Arquivo CSV onde serão salvas as previsões. |
| `--metricas CAMINHO` | `metricas_carga.json` | Arquivo JSON onde serão salvas as métricas. |
| `--horizonte N` | `1` | Horizonte de previsão em semanas. |
| `--graficos CAMINHO` | `graficos_classificacao` | Pasta onde serão salvos os gráficos. |
| `--quantil-graficos VALOR` | `0.98` | Quantil máximo exibido nos gráficos. |
| `--classificacao CAMINHO` | `resultados_classificacao` | Pasta para tabelas de classificação, comparação e SHAP. |

Exemplo com parâmetros personalizados:

```bash
python ml/main.py \
  --dados data/dados_tratados \
  --saida resultados/previsoes_carga.csv \
  --metricas resultados/metricas_carga.json \
  --horizonte 4 \
  --graficos resultados/graficos \
  --quantil-graficos 0.99 \
  --classificacao resultados/classificacao
```

A coluna `faixa_volume` das previsões (baixo, moderado, alto, muito alto) é
definida por limiares históricos: os quantis 0,50 / 0,75 / 0,90 das semanas de
treino com pelo menos uma notificação (hoje 2, 4 e 8 notificações). Ela **não**
vem de clusterização. `metricas_carga.json` traz os limiares, a acurácia e a
matriz de confusão entre faixa observada e faixa prevista.

## 🩹 Qualidade dos dados: códigos das unidades de saúde

Nos arquivos `dengue-2022.csv` e `dengue-2023.csv` o código CNES da unidade
perdeu os zeros à esquerda ("604" em vez de "0000604"). Assim a mesma unidade
aparecia como duas entidades, e a série de cada uma parecia começar ou terminar
na virada de 2023 para 2024. O carregamento (`normalizar_codigo_unidade`, em
`ml/data.py`) agora padroniza todos os códigos com 7 dígitos.

## Conversão dos dados tratados para Parquet

O script `data/dados_tratados/converter_para_parquet.sh` usa o CLI do DuckDB
para converter os CSVs tratados. Ele cria um arquivo `.parquet` ao lado de
cada CSV e mantém os CSVs originais.

Para executar a conversão manualmente:

```bash
cd data/dados_tratados
bash converter_para_parquet.sh
```

Se os arquivos `.parquet` já existirem, remova-os antes de executar novamente:

```bash
rm -- data/dados_tratados/*.parquet
bash data/dados_tratados/converter_para_parquet.sh
```
