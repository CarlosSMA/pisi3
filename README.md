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

Para executar a clusterização das unidades de saúde (detalhada abaixo):

```bash
python ml/clusterizar.py
```

| Flag | Padrão | Descrição |
| --- | --- | --- |
| `--dados CAMINHO` | `data/dados_tratados` | Diretório com os dados tratados. |
| `--saida CAMINHO` | `resultados_clusterizacao` | Pasta para CSVs, JSON e gráficos. |
| `--min-notificacoes N` | `30` | Mínimo de notificações para uma unidade ser agrupada. |
| `--anos ANO [ANO ...]` | todos | Anos considerados, ex.: `--anos 2023 2024 2025`. |

## 🩹 Qualidade dos dados: códigos das unidades de saúde

Nos arquivos `dengue-2022.csv` e `dengue-2023.csv` o código CNES da unidade
perdeu os zeros à esquerda ("604" em vez de "0000604"). Assim a mesma unidade
aparecia como duas entidades, e a série de cada uma parecia começar ou terminar
na virada de 2023 para 2024. O carregamento (`normalizar_codigo_unidade`, em
`ml/data.py`) agora padroniza todos os códigos com 7 dígitos.

## 🧬 Clusterização das unidades de saúde

Código: `ml/clustering.py` (pipeline), `ml/clustering_plots.py` (gráficos) e
`ml/clusterizar.py` (execução).

### O que é agrupado

Cada linha é **uma unidade de saúde notificadora (código CNES)** com pelo menos
30 notificações entre 2022 e 2025: **62 de 453 unidades**, que somam **95% das
notificações**. Cada unidade é descrita por indicadores agregados. Pacientes e
casos individuais **não** são agrupados nem classificados.

### Variáveis

**Ativas** (entram na distância). Cada uma representa uma dimensão diferente do
perfil da unidade, e elas são pouco correlacionadas entre si:

| Variável | Significado |
| --- | --- |
| `log_notificacoes_semana` | Volume: log(1 + notificações por semana) |
| `prop_chikungunya` | Proporção das notificações que são de chikungunya |
| `taxa_hospitalizacao` | Proporção de hospitalizados (entre registros com o campo informado) |
| `idade_media` | Idade média dos pacientes notificados |
| `dispersao_territorial` | Entropia normalizada dos bairros de residência (0 = um só bairro; 1 = uniforme) |
| `crescimento_24_25` | log((notificações 2024–25 + 1) / (notificações 2022–23 + 1)) |

**Ilustrativas** (só descrevem os clusters): `taxa_confirmacao`,
`completude_registro`, `atraso_notificacao_mediano`,
`tempo_encerramento_mediano`, `cv_semanal` e `prop_zika`. Elas medem o processo
de notificação e registro, e não o perfil da unidade, ou são redundantes
(`cv_semanal` tem r = −0,55 com o volume). Com as 12 variáveis juntas, a melhor
silhueta cai de 0,32 para 0,22 e a estabilidade cai de 0,84 para 0,55. A
comparação entre os dois conjuntos fica registrada em `selecao_variaveis` no
JSON.

**Excluídas:** `caso_grave` (14 casos) e `obito` (7 casos), raros demais para
diferenciar unidades; `prop_dengue`, que é o complemento de chikungunya + zika.
Não há variáveis categóricas, então a distância euclidiana é adequada.

### Redução de dimensionalidade

PCA sobre as variáveis padronizadas, mantendo o **menor número de componentes
com ≥ 80% da variância acumulada**: **4 componentes, 82,9%** (gráficos
`02_pca_variancia` e `03_pca_cargas`). Os algoritmos rodam nesse espaço. A
partição do K-Means no espaço PCA é praticamente a mesma do espaço completo
(ARI = 0,79). O t-SNE é usado **apenas para visualização**.

### Algoritmos e escolha de parâmetros

| Algoritmo | Como os parâmetros foram escolhidos | Resultado |
| --- | --- | --- |
| **K-Means** | k de 2 a 10. Critério: maior silhueta. Apoio: cotovelo e estabilidade (ARI médio em 30 subamostras de 80%) | **k = 5**, silhueta 0,32, estabilidade 0,84 (a maior entre os k) |

### Resultados (K-Means, k = 5)

| Cluster | Unidades | Notificações | % hospitalização | Idade média | Dispersão territorial | Crescimento 24–25 (×) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 · Abrangência local | 16 | 4.761 | 4,6 | 33,2 | 0,39 | 2,1 |
| 2 · Notificação recente (2024–25) | 15 | 3.162 | 13,3 | 32,0 | 0,71 | 13,8 |
| 3 · Alto volume | 15 | 20.452 (60%) | 3,5 | 32,9 | 0,68 | 2,1 |
| 4 · Perfil hospitalar | 10 | 1.752 | 64,6 | 33,4 | 0,78 | 1,8 |
| 5 · Perfil pediátrico | 6 | 4.204 | 23,4 | 9,9 | 0,77 | 2,4 |

O nome de cada cluster é gerado automaticamente a partir da variável ativa com
maior |z-score| médio (gráfico `11_perfil_clusters`).

### Arquivos gerados (`resultados_clusterizacao/`)

| Arquivo | Conteúdo |
| --- | --- |
| `perfil_unidades.csv` | Variáveis, rótulos do K-Means e coordenadas PCA e t-SNE por unidade |
| `metricas_clusterizacao.json` | Relatório completo: variáveis, pré-processamento, buscas de parâmetros, comparações e perfis dos clusters |
| `graficos/*.png` | Gráficos numerados na ordem da análise |

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
