# Diferenças de estrutura dos arquivos CSV

## Objetivo

Este documento compara os 12 arquivos epidemiológicos de `data/` sem alterar seus conteúdos. A comparação considera o cabeçalho literal, a versão normalizada dos nomes (`lowercase` e remoção apenas da diferença de caixa) e a quantidade de campos por linha.

## Resumo geral

| Doença | Arquivos | Faixa de colunas | Registros totais | Padrão de encoding | Separador |
|---|---:|---:|---:|---|---|
| Chikungunya | 4 | 125 a 143 | 8.088 | UTF-8 com BOM | `;` |
| Dengue | 4 | 130 | 26.164 | UTF-8 com BOM | `;` |
| Zika | 4 | 47 | 1.738 | UTF-8 com BOM | `;` |

Todos os arquivos usam `;` como separador e foram lidos como `utf-8-sig`. Nenhum arquivo apresentou, no inventário inicial, linhas com quantidade de campos diferente da largura declarada.

## Inventário comparativo

| Arquivo | Colunas | Registros | Diferença estrutural principal |
|---|---:|---:|---|
| `chikungunya-2022.csv` | 125 | 2.110 | Estrutura-base de Chikungunya. |
| `chikungunya-2023.csv` | 125 | 1.555 | Igual a 2022. |
| `chikungunya-2024.csv` | 143 | 2.481 | `COMPLICA` e 17 cabeçalhos vazios ao final. |
| `chikungunya-2025.csv` | 130 | 1.942 | `HOSPITAL`, `DDD_HOSP`, `TEL_HOSP`, `COMPLICA`, `NU_LOTE_I` e `DS_OBS`; ausência de `CS_ZONA`. |
| `dengue-2022.csv` | 130 | 2.906 | Cabeçalhos em maiúsculas; estrutura-base de Dengue. |
| `dengue-2023.csv` | 130 | 3.523 | Cabeçalhos em minúsculas; ausência de `CS_ZONA`; presença de `DS_OBS`. |
| `dengue-2024.csv` | 130 | 10.548 | Cabeçalhos em maiúsculas; ausência de `CS_ZONA`; presença de `DS_OBS`. |
| `dengue-2025.csv` | 130 | 9.187 | Cabeçalhos em maiúsculas; ausência de `CS_ZONA`; presença de `DS_OBS`. |
| `zika-2022.csv` | 47 | 216 | Esquema curto de Zika. |
| `zika-2023.csv` | 47 | 226 | Igual a 2022. |
| `zika-2024.csv` | 47 | 475 | Igual a 2022. |
| `zika-2025.csv` | 47 | 821 | Igual a 2022. |

## Diferenças por doença

### Chikungunya

- 2022 e 2023 têm o mesmo conjunto, ordem e caixa de 125 colunas.
- 2024 tem 143 posições de cabeçalho: mantém os campos-base, acrescenta `COMPLICA` e possui 17 nomes vazios no final.
- 2025 tem 130 colunas: acrescenta `HOSPITAL`, `DDD_HOSP`, `TEL_HOSP`, `COMPLICA`, `NU_LOTE_I` e `DS_OBS`, sem `CS_ZONA`.
- Os nomes vazios de 2024 não devem ser transformados em uma coluna chamada `Unnamed` sem registro explícito da inconsistência.

### Dengue

- Todos os anos têm 130 colunas.
- 2022 usa nomes em maiúsculas.
- 2023 usa nomes em minúsculas.
- 2024 e 2025 voltam a usar nomes em maiúsculas, mas conservam `DS_OBS` e não possuem `CS_ZONA`.
- A diferença de caixa não representa novas variáveis; deve ser tratada como variação de exportação.
- `CS_ZONA` e `DS_OBS` não são equivalentes semanticamente e não devem ser alinhados apenas por posição.

### Zika

- Os quatro anos têm exatamente 47 colunas.
- Os cabeçalhos têm o mesmo conjunto e a mesma ordem.
- `CS_SUSPEIT`, `NDUPLIC_N` e `IN_VINCULA` caracterizam esse esquema reduzido.
- Não há colunas extras ou ausentes entre os anos de Zika.

## Diferenças entre doenças

| Comparação | Resultado |
|---|---|
| Chikungunya e Dengue | Compartilham grande parte do formulário de arboviroses, mas Chikungunya varia entre 125 e 143 campos, enquanto Dengue tem 130 e possui variações de `CS_ZONA`/`DS_OBS`. |
| Chikungunya e Zika | Zika não possui os blocos extensos de sintomas, exames, sinais de alarme e gravidade presentes em Chikungunya. |
| Dengue e Zika | Zika possui 47 campos e inclui `CS_SUSPEIT`, `NDUPLIC_N` e `IN_VINCULA`; Dengue possui 130 campos e blocos clínicos/laboratoriais adicionais. |

## Campos que não devem ser alinhados automaticamente

Os seguintes pares ou grupos exigem mapeamento explícito:

| Campo ou grupo | Motivo |
|---|---|
| `CS_ZONA` / `DS_OBS` | Ocupam posição comparável em alguns cabeçalhos, mas representam zona de residência e observação textual. |
| `CO_BAINF` / `CO_BAINFC` | Variação de nome entre esquemas de residência/infecção; deve ser documentada antes da união. |
| Maiúsculas/minúsculas em Dengue 2023 | É a mesma convenção de campo apenas quando a comparação normalizada confirmar o nome, sem alterar o nome original. |
| Campos vazios de Chikungunya 2024 | Não representam variáveis identificáveis; devem permanecer registrados como posições vazias do cabeçalho. |
| Campos herdados de outras fichas | Nomes como `DT_CHIK_S1` ou `CLINC_CHIK` não devem ser removidos só porque aparecem no arquivo de Dengue. |

## Regras para consolidação

1. Preservar os CSVs originais e seus nomes de coluna.
2. Criar uma chave normalizada apenas para comparação e nunca usá-la para apagar a grafia original.
3. Consolidar Chikungunya 2022/2023 como uma variante de 125 campos.
4. Manter Chikungunya 2024 separado até que os 17 cabeçalhos vazios sejam esclarecidos.
5. Tratar Chikungunya 2025 como variante própria por causa dos seis campos extras e da ausência de `CS_ZONA`.
6. Consolidar Dengue somente após resolver explicitamente `CS_ZONA` versus `DS_OBS`.
7. Consolidar os quatro anos de Zika quanto ao esquema, mantendo o ano como dimensão do registro.
8. Não preencher colunas ausentes com valores vazios sem registrar essa operação na documentação de transformação.
9. Ler identificadores e códigos como texto para preservar zeros à esquerda.

## Limites desta comparação

Este documento trata diferenças de estrutura, não valida ainda os domínios, tipos observados, percentuais de nulos ou formatos de cada valor. Esses itens serão documentados na próxima etapa, em `docs/inconsistencias_dados.md`.