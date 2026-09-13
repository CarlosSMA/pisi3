# Dicionário de dados: Dengue

## Escopo

Este documento descreve os quatro arquivos de Dengue disponíveis em `data/`:

- `dengue-2022.csv`
- `dengue-2023.csv`
- `dengue-2024.csv`
- `dengue-2025.csv`

Os arquivos registram notificações epidemiológicas relacionadas à Dengue. Os nomes dos campos são mantidos como aparecem em cada arquivo. Para comparar os anos, os nomes foram avaliados também sem distinção entre maiúsculas e minúsculas.

## Inventário dos arquivos

| Arquivo | Ano | Colunas declaradas | Registros | Encoding detectado | Separador | Linhas com largura divergente |
|---|---:|---:|---:|---|---|---:|
| `dengue-2022.csv` | 2022 | 130 | 2.906 | UTF-8 com BOM | `;` | 0 |
| `dengue-2023.csv` | 2023 | 130 | 3.523 | UTF-8 com BOM | `;` | 0 |
| `dengue-2024.csv` | 2024 | 130 | 10.548 | UTF-8 com BOM | `;` | 0 |
| `dengue-2025.csv` | 2025 | 130 | 9.187 | UTF-8 com BOM | `;` | 0 |

## Equivalência estrutural

Os quatro arquivos têm a mesma quantidade de colunas e o mesmo conjunto normalizado de nomes, com duas diferenças importantes:

1. `dengue-2022.csv` usa cabeçalhos em maiúsculas, por exemplo `NU_NOTIFIC` e `DT_NOTIFIC`.
2. `dengue-2023.csv`, `dengue-2024.csv` e `dengue-2025.csv` usam cabeçalhos em minúsculas, por exemplo `nu_notific` e `dt_notific`.
3. No conjunto normalizado, os arquivos de 2023 a 2025 apresentam `ds_obs` onde 2022 apresenta `cs_zona`. Isso deve ser tratado como diferença semântica de campo, não apenas como diferença de caixa.

Portanto, os anos podem ser consolidados para análise apenas depois de um mapeamento explícito. Não se deve concatenar os arquivos por posição sem primeiro normalizar os nomes e resolver a substituição `CS_ZONA`/`ds_obs`.

## Campos do esquema de 2022

O cabeçalho completo de 2022 é:

```text
NU_NOTIFIC, TP_NOT, ID_AGRAVO, DT_NOTIFIC, SEM_NOT, NU_ANO, SG_UF_NOT, ID_MUNICIP, ID_REGIONA, ID_UNIDADE, DT_SIN_PRI, SEM_PRI, DT_NASC, NU_IDADE_N, CS_SEXO, CS_GESTANT, CS_RACA, CS_ESCOL_N, SG_UF, ID_MN_RESI, ID_RG_RESI, ID_DISTRIT, ID_BAIRRO, NM_BAIRRO, ID_LOGRADO, NM_LOGRADO, NU_CEP, CS_ZONA, ID_PAIS, DT_INVEST, ID_OCUPA_N, FEBRE, MIALGIA, CEFALEIA, EXANTEMA, VOMITO, NAUSEA, DOR_COSTAS, CONJUNTVIT, ARTRITE, ARTRALGIA, PETEQUIA_N, LEUCOPENIA, LACO, DOR_RETRO, DIABETES, HEMATOLOG, HEPATOPAT, RENAL, HIPERTENSA, ACIDO_PEPT, AUTO_IMUNE, DT_CHIK_S1, DT_CHIK_S2, DT_PRNT, RES_CHIKS1, RES_CHIKS2, RESUL_PRNT, DT_SORO, RESUL_SORO, DT_NS1, RESUL_NS1, DT_VIRAL, RESUL_VI_N, DT_PCR, RESUL_PCR_, SOROTIPO, HISTOPA_N, IMUNOH_N, HOSPITALIZ, DT_INTERNA, UF, MUNICIPIO, HOSPITAL, DDD_HOSP, TEL_HOSP, TPAUTOCTO, COUFINF, COPAISINF, COMUNINF, CODISINF, CO_BAINF, NOBAIINF, CLASSI_FIN, CRITERIO, DOENCA_TRA, CLINC_CHIK, EVOLUCAO, DT_OBITO, DT_ENCERRA, ALRM_HIPOT, ALRM_PLAQ, ALRM_VOM, ALRM_SANG, ALRM_HEMAT, ALRM_ABDOM, ALRM_LETAR, ALRM_HEPAT, ALRM_LIQ, DT_ALRM, GRAV_PULSO, GRAV_CONV, GRAV_ENCH, GRAV_INSUF, GRAV_TAQUI, GRAV_EXTRE, GRAV_HIPOT, GRAV_HEMAT, GRAV_MELEN, GRAV_METRO, GRAV_SANG, GRAV_AST, GRAV_MIOC, GRAV_CONSC, GRAV_ORGAO, DT_GRAV, MANI_HEMOR, EPISTAXE, GENGIVO, METRO, PETEQUIAS, HEMATURA, SANGRAM, LACO_N, PLASMATICO, EVIDENCIA, PLAQ_MENOR, CON_FHD, COMPLICA, NU_LOTE_I
```

## Descrição dos grupos de campos

| Grupo | Campos | O que representam |
|---|---|---|
| Identificação e notificação | `NU_NOTIFIC`, `TP_NOT`, `ID_AGRAVO`, `NU_ANO` | Identificador, tipo da notificação, código do agravo e ano. |
| Datas e semanas | `DT_NOTIFIC`, `SEM_NOT`, `DT_SIN_PRI`, `SEM_PRI`, `DT_NASC`, `DT_INVEST`, `DT_CHIK_S1`, `DT_CHIK_S2`, `DT_PRNT`, `DT_SORO`, `DT_NS1`, `DT_VIRAL`, `DT_PCR`, `DT_INTERNA`, `DT_OBITO`, `DT_ENCERRA`, `DT_ALRM`, `DT_GRAV` | Datas de notificação, sintomas, nascimento, investigação, exames, internação e encerramento. Alguns nomes são herdados do formulário compartilhado com arboviroses. |
| Localização | `SG_UF_NOT`, `ID_MUNICIP`, `ID_REGIONA`, `ID_UNIDADE`, `SG_UF`, `ID_MN_RESI`, `ID_RG_RESI`, `ID_DISTRIT`, `ID_BAIRRO`, `NM_BAIRRO`, `ID_LOGRADO`, `NM_LOGRADO`, `NU_CEP`, `CS_ZONA`, `ID_PAIS` | Local de notificação e residência. |
| Perfil | `NU_IDADE_N`, `CS_SEXO`, `CS_GESTANT`, `CS_RACA`, `CS_ESCOL_N`, `ID_OCUPA_N` | Idade codificada, sexo, gestação, raça/cor, escolaridade e ocupação. |
| Sintomas e comorbidades | `FEBRE`, `MIALGIA`, `CEFALEIA`, `EXANTEMA`, `VOMITO`, `NAUSEA`, `DOR_COSTAS`, `CONJUNTVIT`, `ARTRITE`, `ARTRALGIA`, `PETEQUIA_N`, `LEUCOPENIA`, `LACO`, `DOR_RETRO`, `DIABETES`, `HEMATOLOG`, `HEPATOPAT`, `RENAL`, `HIPERTENSA`, `ACIDO_PEPT`, `AUTO_IMUNE` | Sinais, sintomas e condições preexistentes registrados na ficha. |
| Laboratório | `RES_CHIKS1`, `RES_CHIKS2`, `RESUL_PRNT`, `RESUL_SORO`, `RESUL_NS1`, `RESUL_VI_N`, `RESUL_PCR_`, `SOROTIPO`, `HISTOPA_N`, `IMUNOH_N` | Resultados laboratoriais e sorotipo, quando preenchidos. |
| Assistência e hospitalização | `HOSPITALIZ`, `DT_INTERNA`, `HOSPITAL`, `DDD_HOSP`, `TEL_HOSP` | Hospitalização, data e dados de contato do hospital. |
| Infecção e classificação | `UF`, `MUNICIPIO`, `TPAUTOCTO`, `COUFINF`, `COPAISINF`, `COMUNINF`, `CODISINF`, `CO_BAINF`, `NOBAIINF`, `CLASSI_FIN`, `CRITERIO`, `DOENCA_TRA`, `CLINC_CHIK`, `EVOLUCAO` | Local provável, autoctonia, classificação final, critério, evolução e campos clínicos herdados. |
| Gravidade e manifestações | `ALRM_HIPOT`, `ALRM_PLAQ`, `ALRM_VOM`, `ALRM_SANG`, `ALRM_HEMAT`, `ALRM_ABDOM`, `ALRM_LETAR`, `ALRM_HEPAT`, `ALRM_LIQ`, `GRAV_PULSO`, `GRAV_CONV`, `GRAV_ENCH`, `GRAV_INSUF`, `GRAV_TAQUI`, `GRAV_EXTRE`, `GRAV_HIPOT`, `GRAV_HEMAT`, `GRAV_MELEN`, `GRAV_METRO`, `GRAV_SANG`, `GRAV_AST`, `GRAV_MIOC`, `GRAV_CONSC`, `GRAV_ORGAO`, `MANI_HEMOR`, `EPISTAXE`, `GENGIVO`, `METRO`, `PETEQUIAS`, `HEMATURA`, `SANGRAM`, `LACO_N`, `PLASMATICO`, `EVIDENCIA`, `PLAQ_MENOR`, `CON_FHD` | Sinais de alarme, gravidade, manifestações hemorrágicas e condições relacionadas. |
| Controle e observação | `COMPLICA`, `NU_LOTE_I`, `ds_obs` | Complicações, lote e observação textual. `ds_obs` aparece com esse nome apenas nos arquivos de 2023 a 2025. |

## Tipos e domínios observáveis

Os campos são predominantemente códigos categóricos, identificadores textuais, datas ou texto livre. Valores como `1`, `2`, `4`, `5`, `9` e `10` em sintomas, classificação e evolução devem ser interpretados segundo os domínios da ficha, não como medidas quantitativas.

Exemplos reais observados:

| Campo | Exemplo |
|---|---|
| `NU_NOTIFIC` | `4197816` |
| `ID_AGRAVO` | `A90` |
| `DT_NOTIFIC` | `2022-01-03` |
| `CS_SEXO` | `F` |
| `NM_BAIRRO` | `ESTANCIA` |
| `CS_ZONA` | `1` |
| `CLASSI_FIN` | `5` |
| `ds_obs` | `SEM COLETA DE EXAME NO GAL` |

Identificadores como `NU_NOTIFIC`, `ID_UNIDADE`, `NU_CEP` e códigos territoriais devem ser lidos como texto para preservar zeros à esquerda. Os arquivos de 2023 apresentam valores com aparência decimal, como `2.0` e `2023.0`, em campos originalmente codificados; isso precisa ser registrado na análise de qualidade e não corrigido silenciosamente nesta etapa.

## Diferenças e cuidados

| Aspecto | Observação |
|---|---|
| Caixa dos nomes | 2022 usa maiúsculas; 2023–2025 usam minúsculas. |
| `CS_ZONA` versus `ds_obs` | São campos diferentes, apesar de ocuparem a mesma posição relativa no cabeçalho. Não devem ser tratados como equivalentes. |
| Campos hospitalares | `HOSPITAL`, `DDD_HOSP` e `TEL_HOSP` estão presentes no esquema documentado; devem ser conferidos por ano durante a análise final. |
| Formato de datas | 2022 e 2023 exibem datas ISO em amostras; as versões posteriores podem conter datas serializadas ou formatos diferentes. A validação por coluna será feita no gerador final. |
| Texto livre | `ds_obs` pode conter mensagens clínicas e administrativas. Deve permanecer texto, com nulos contabilizados separadamente. |
| Campos herdados | Vários nomes relacionados a Chikungunya, como `DT_CHIK_S1` e `CLINC_CHIK`, aparecem na ficha de Dengue. O dicionário deve documentar o campo como publicado, sem inferir que foi preenchido para Dengue. |