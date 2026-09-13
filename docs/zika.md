# Dicionário de dados: Zika

## Escopo

Este documento descreve os quatro arquivos de Zika disponíveis em `data/`:

- `zika-2022.csv`
- `zika-2023.csv`
- `zika-2024.csv`
- `zika-2025.csv`

Os arquivos registram notificações epidemiológicas de casos suspeitos ou investigados de Zika. Os nomes das colunas são preservados como aparecem nos CSVs.

## Inventário dos arquivos

| Arquivo | Ano | Colunas | Registros | Encoding detectado | Separador | Linhas com largura divergente |
|---|---:|---:|---:|---|---|---:|
| `zika-2022.csv` | 2022 | 47 | 216 | UTF-8 com BOM | `;` | 0 |
| `zika-2023.csv` | 2023 | 47 | 226 | UTF-8 com BOM | `;` | 0 |
| `zika-2024.csv` | 2024 | 47 | 475 | UTF-8 com BOM | `;` | 0 |
| `zika-2025.csv` | 2025 | 47 | 821 | UTF-8 com BOM | `;` | 0 |

## Estrutura comum

Os quatro arquivos possuem exatamente 47 colunas, com o mesmo conjunto e a mesma ordem de nomes. Não foram identificadas colunas adicionais ou ausentes entre os anos.

| Coluna | Descrição | Grupo |
|---|---|---|
| `NU_NOTIFIC` | Número identificador da notificação. | Identificação |
| `TP_NOT` | Tipo da notificação. | Identificação |
| `ID_AGRAVO` | Código do agravo/CID registrado. | Identificação |
| `CS_SUSPEIT` | Código ou indicador relacionado à suspeita de Zika. | Investigação |
| `DT_NOTIFIC` | Data de notificação do caso. | Datas |
| `SEM_NOT` | Semana epidemiológica da notificação. | Datas |
| `NU_ANO` | Ano da notificação. | Datas |
| `SG_UF_NOT` | Código da UF de notificação. | Localização |
| `ID_MUNICIP` | Código do município de notificação. | Localização |
| `ID_REGIONA` | Código da regional de saúde. | Localização |
| `ID_UNIDADE` | Código do estabelecimento notificante. | Localização |
| `DT_SIN_PRI` | Data dos primeiros sintomas. | Datas |
| `SEM_PRI` | Semana epidemiológica dos primeiros sintomas. | Datas |
| `DT_NASC` | Data de nascimento. | Perfil |
| `NU_IDADE_N` | Idade codificada conforme a ficha. | Perfil |
| `CS_SEXO` | Sexo informado. | Perfil |
| `CS_GESTANT` | Situação gestacional. | Perfil |
| `CS_RACA` | Raça/cor informada. | Perfil |
| `CS_ESCOL_N` | Escolaridade informada. | Perfil |
| `SG_UF` | Código da UF de residência. | Residência |
| `ID_MN_RESI` | Código do município de residência. | Residência |
| `ID_RG_RESI` | Código da regional de residência. | Residência |
| `ID_DISTRIT` | Código do distrito de residência. | Residência |
| `ID_BAIRRO` | Código do bairro de residência. | Residência |
| `NM_BAIRRO` | Nome do bairro de residência. | Residência |
| `ID_LOGRADO` | Código do logradouro. | Residência |
| `NM_LOGRADO` | Nome do logradouro. | Residência |
| `NU_CEP` | Código postal informado. | Residência |
| `CS_ZONA` | Zona de residência. | Residência |
| `ID_PAIS` | Código do país de residência. | Residência |
| `NDUPLIC_N` | Indicador ou código de duplicidade da notificação. | Controle |
| `IN_VINCULA` | Indicador de vinculação com outro registro. | Controle |
| `DT_INVEST` | Data de investigação ou inclusão da notificação. | Datas |
| `ID_OCUPA_N` | Código da ocupação. | Perfil |
| `CLASSI_FIN` | Classificação final do caso. | Encerramento |
| `CRITERIO` | Critério de confirmação, descarte ou investigação. | Encerramento |
| `TPAUTOCTO` | Tipo de autoctonia. | Infecção |
| `COUFINF` | Código da UF de infecção. | Infecção |
| `COPAISINF` | Código do país de infecção. | Infecção |
| `COMUNINF` | Código do município de infecção. | Infecção |
| `CODISINF` | Código do distrito de infecção. | Infecção |
| `CO_BAINFC` | Código do bairro de infecção. | Infecção |
| `NOBAIINF` | Nome do bairro de infecção. | Infecção |
| `DOENCA_TRA` | Doença relacionada ou traço associado. | Encerramento |
| `EVOLUCAO` | Evolução do caso. | Encerramento |
| `DT_OBITO` | Data do óbito, quando informada. | Encerramento |
| `DT_ENCERRA` | Data de encerramento da investigação. | Encerramento |

## Diferenças em relação às outras doenças

Zika possui um esquema reduzido de 47 campos. Não há, nesses arquivos, os blocos extensos de sintomas, comorbidades, exames laboratoriais, sinais de alarme e gravidade encontrados nos arquivos de Chikungunya e Dengue.

Os campos `CS_SUSPEIT`, `NDUPLIC_N` e `IN_VINCULA` são específicos do esquema de Zika entre os três conjuntos documentados. Essa diferença deve ser preservada na consolidação geral, sem criar colunas vazias artificialmente para simular um esquema comum.

## Tipos e domínios observáveis

Os campos de identificação, localização e controle devem ser tratados como códigos ou texto, mesmo quando os valores contêm apenas dígitos. Isso preserva zeros à esquerda em identificadores como `ID_UNIDADE`, `NU_CEP` e códigos territoriais.

Os campos de sintomas não estão presentes neste esquema. Os códigos de `CS_SUSPEIT`, `TP_NOT`, `CS_GESTANT`, `CS_RACA`, `CS_ESCOL_N`, `CLASSI_FIN`, `CRITERIO`, `TPAUTOCTO`, `EVOLUCAO`, `NDUPLIC_N` e `IN_VINCULA` devem ser documentados como categorias observadas, e não como medidas quantitativas.

Exemplos reais observados:

| Campo | Exemplo |
|---|---|
| `NU_NOTIFIC` | `4203803` |
| `TP_NOT` | `2` |
| `ID_AGRAVO` | `A928` |
| `CS_SUSPEIT` | vazio no primeiro registro consultado |
| `DT_NOTIFIC` | `19/1/2022` |
| `CS_SEXO` | `F` |
| `NM_BAIRRO` | `JORDAO` |
| `CLASSI_FIN` | `2` |
| `EVOLUCAO` | `1` |

## Observações por ano

| Ano | Observação |
|---:|---|
| 2022 | 216 registros, esquema completo de 47 campos. |
| 2023 | 226 registros, mesmo esquema de 47 campos. |
| 2024 | 475 registros, mesmo esquema de 47 campos; as amostras usam datas no formato ISO. |
| 2025 | 821 registros, mesmo esquema de 47 campos; as amostras usam datas com dia e mês preenchidos com dois dígitos. |

As datas apresentam variação de representação entre anos, como `19/1/2022` e `2024-02-28`. A análise final deve contabilizar os formatos por coluna e ano, sem normalizar os valores de origem neste documento.