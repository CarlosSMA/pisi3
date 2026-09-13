# Dicionário de dados: Chikungunya

## Escopo

Este documento descreve os arquivos de Chikungunya disponíveis em `data/`:

- `chikungunya-2022.csv`
- `chikungunya-2023.csv`
- `chikungunya-2024.csv`
- `chikungunya-2025.csv`

Os arquivos representam registros de notificações epidemiológicas. Os nomes abaixo são os nomes reais dos cabeçalhos, preservados sem renomeação. As descrições usam os dicionários de referência em `data/dict/dict_chikungunya.json` quando há correspondência; nos demais casos, são descrições operacionais baseadas no nome do campo e no agrupamento da ficha.

## Inventário dos arquivos

| Arquivo | Ano | Colunas declaradas | Registros | Encoding detectado | Separador | Linhas com largura divergente |
|---|---:|---:|---:|---|---|---:|
| `chikungunya-2022.csv` | 2022 | 125 | 2.110 | UTF-8 com BOM | `;` | 0 |
| `chikungunya-2023.csv` | 2023 | 125 | 1.555 | UTF-8 com BOM | `;` | 0 |
| `chikungunya-2024.csv` | 2024 | 143 | 2.481 | UTF-8 com BOM | `;` | 0 |
| `chikungunya-2025.csv` | 2025 | 130 | 1.942 | UTF-8 com BOM | `;` | 0 |

## Estrutura comum

Os arquivos de 2022 e 2023 possuem exatamente o mesmo cabeçalho, com 125 campos. Esse conjunto é a estrutura-base usada para comparar 2024 e 2025.

| Coluna | Descrição operacional | Grupo |
|---|---|---|
| `NU_NOTIFIC` | Número identificador da notificação. | Identificação |
| `TP_NOT` | Tipo da notificação. | Identificação |
| `ID_AGRAVO` | Código do agravo/CID registrado. | Identificação |
| `DT_NOTIFIC` | Data de preenchimento ou notificação do caso. | Datas |
| `SEM_NOT` | Semana epidemiológica da notificação. | Datas |
| `NU_ANO` | Ano da notificação. | Datas |
| `SG_UF_NOT` | Código da unidade federativa de notificação. | Localização |
| `ID_MUNICIP` | Código do município de notificação. | Localização |
| `ID_REGIONA` | Código da regional de saúde. | Localização |
| `ID_UNIDADE` | Código do estabelecimento de saúde notificante. | Localização |
| `DT_SIN_PRI` | Data dos primeiros sintomas. | Datas |
| `SEM_PRI` | Semana epidemiológica dos primeiros sintomas. | Datas |
| `DT_NASC` | Data de nascimento. | Perfil |
| `NU_IDADE_N` | Idade codificada conforme a ficha de notificação. | Perfil |
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
| `DT_INVEST` | Data de investigação ou inclusão da notificação. | Datas |
| `ID_OCUPA_N` | Código da ocupação. | Perfil |
| `FEBRE` | Registro de febre. | Sintomas |
| `MIALGIA` | Registro de mialgia. | Sintomas |
| `CEFALEIA` | Registro de cefaleia. | Sintomas |
| `EXANTEMA` | Registro de exantema. | Sintomas |
| `VOMITO` | Registro de vômito. | Sintomas |
| `NAUSEA` | Registro de náusea. | Sintomas |
| `DOR_COSTAS` | Registro de dor nas costas. | Sintomas |
| `CONJUNTVIT` | Registro de conjuntivite. | Sintomas |
| `ARTRITE` | Registro de artrite. | Sintomas |
| `ARTRALGIA` | Registro de artralgia. | Sintomas |
| `PETEQUIA_N` | Registro de petéquias. | Sintomas |
| `LEUCOPENIA` | Registro de leucopenia. | Sintomas |
| `LACO` | Resultado ou realização da prova do laço. | Sintomas |
| `DOR_RETRO` | Registro de dor retro-orbital. | Sintomas |
| `DIABETES` | Comorbidade diabetes. | Comorbidades |
| `HEMATOLOG` | Comorbidade ou alteração hematológica. | Comorbidades |
| `HEPATOPAT` | Comorbidade hepática. | Comorbidades |
| `RENAL` | Comorbidade ou alteração renal. | Comorbidades |
| `HIPERTENSA` | Comorbidade hipertensão arterial. | Comorbidades |
| `ACIDO_PEPT` | Registro de doença ácido-péptica. | Comorbidades |
| `AUTO_IMUNE` | Registro de doença autoimune. | Comorbidades |
| `DT_CHIK_S1` | Data da coleta ou exame Chikungunya S1. | Laboratório |
| `DT_CHIK_S2` | Data da coleta ou exame Chikungunya S2. | Laboratório |
| `DT_PRNT` | Data do exame PRNT. | Laboratório |
| `RES_CHIKS1` | Resultado do exame Chikungunya S1. | Laboratório |
| `RES_CHIKS2` | Resultado do exame Chikungunya S2. | Laboratório |
| `RESUL_PRNT` | Resultado do exame PRNT. | Laboratório |
| `DT_SORO` | Data da sorologia. | Laboratório |
| `RESUL_SORO` | Resultado da sorologia. | Laboratório |
| `DT_NS1` | Data do teste NS1. | Laboratório |
| `RESUL_NS1` | Resultado do teste NS1. | Laboratório |
| `DT_VIRAL` | Data do exame viral. | Laboratório |
| `RESUL_VI_N` | Resultado do exame viral. | Laboratório |
| `DT_PCR` | Data do exame PCR. | Laboratório |
| `RESUL_PCR_` | Resultado do exame PCR. | Laboratório |
| `SOROTIPO` | Sorotipo identificado. | Laboratório |
| `HISTOPA_N` | Resultado de histopatologia. | Laboratório |
| `IMUNOH_N` | Resultado de imuno-histoquímica. | Laboratório |
| `HOSPITALIZ` | Indicador de hospitalização. | Assistência |
| `DT_INTERNA` | Data de internação. | Assistência |
| `UF` | UF relacionada ao local de infecção ou investigação. | Infecção |
| `MUNICIPIO` | Município relacionado ao local de infecção ou investigação. | Infecção |
| `TPAUTOCTO` | Tipo de autoctonia. | Infecção |
| `COUFINF` | Código da UF de infecção. | Infecção |
| `COPAISINF` | Código do país de infecção. | Infecção |
| `COMUNINF` | Código do município de infecção. | Infecção |
| `CODISINF` | Código do distrito de infecção. | Infecção |
| `CO_BAINF` | Código do bairro de infecção. | Infecção |
| `NOBAIINF` | Nome do bairro de infecção. | Infecção |
| `CLASSI_FIN` | Classificação final do caso. | Encerramento |
| `CRITERIO` | Critério de confirmação ou descarte. | Encerramento |
| `DOENCA_TRA` | Doença relacionada ou traço associado. | Encerramento |
| `CLINC_CHIK` | Classificação clínica da Chikungunya. | Encerramento |
| `EVOLUCAO` | Evolução do caso. | Encerramento |
| `DT_OBITO` | Data do óbito, quando informada. | Encerramento |
| `DT_ENCERRA` | Data de encerramento da investigação. | Encerramento |
| `ALRM_HIPOT` | Sinal de alarme: hipotensão. | Sinais de alarme |
| `ALRM_PLAQ` | Sinal de alarme: plaquetopenia. | Sinais de alarme |
| `ALRM_VOM` | Sinal de alarme: vômitos. | Sinais de alarme |
| `ALRM_SANG` | Sinal de alarme: sangramento. | Sinais de alarme |
| `ALRM_HEMAT` | Sinal de alarme: alteração hematológica. | Sinais de alarme |
| `ALRM_ABDOM` | Sinal de alarme: dor abdominal. | Sinais de alarme |
| `ALRM_LETAR` | Sinal de alarme: letargia. | Sinais de alarme |
| `ALRM_HEPAT` | Sinal de alarme: alteração hepática. | Sinais de alarme |
| `ALRM_LIQ` | Sinal de alarme relacionado a líquidos. | Sinais de alarme |
| `DT_ALRM` | Data do registro de sinais de alarme. | Sinais de alarme |
| `GRAV_PULSO` | Gravidade: alteração de pulso. | Gravidade |
| `GRAV_CONV` | Gravidade: convulsão. | Gravidade |
| `GRAV_ENCH` | Gravidade: alteração do enchimento capilar. | Gravidade |
| `GRAV_INSUF` | Gravidade: insuficiência. | Gravidade |
| `GRAV_TAQUI` | Gravidade: taquicardia. | Gravidade |
| `GRAV_EXTRE` | Gravidade: extremidades frias. | Gravidade |
| `GRAV_HIPOT` | Gravidade: hipotensão. | Gravidade |
| `GRAV_HEMAT` | Gravidade: manifestação hematológica. | Gravidade |
| `GRAV_MELEN` | Gravidade: melena. | Gravidade |
| `GRAV_METRO` | Gravidade: metrorragia. | Gravidade |
| `GRAV_SANG` | Gravidade: sangramento. | Gravidade |
| `GRAV_AST` | Gravidade: alteração de AST. | Gravidade |
| `GRAV_MIOC` | Gravidade: miocardite. | Gravidade |
| `GRAV_CONSC` | Gravidade: alteração de consciência. | Gravidade |
| `GRAV_ORGAO` | Gravidade: comprometimento de órgão. | Gravidade |
| `DT_GRAV` | Data do registro de gravidade. | Gravidade |
| `MANI_HEMOR` | Manifestação hemorrágica. | Manifestações |
| `EPISTAXE` | Epistaxe. | Manifestações |
| `GENGIVO` | Sangramento gengival. | Manifestações |
| `METRO` | Metrorragia. | Manifestações |
| `PETEQUIAS` | Petéquias. | Manifestações |
| `HEMATURA` | Hematúria. | Manifestações |
| `SANGRAM` | Sangramento em geral. | Manifestações |
| `LACO_N` | Resultado complementar da prova do laço. | Manifestações |
| `PLASMATICO` | Extravasamento ou alteração plasmática. | Manifestações |
| `EVIDENCIA` | Evidência laboratorial ou clínica registrada. | Manifestações |
| `PLAQ_MENOR` | Registro de plaquetas abaixo do limite. | Manifestações |
| `CON_FHD` | Condição compatível com febre hemorrágica da dengue. | Manifestações |

## Campos adicionados ou problemáticos por ano

| Arquivo | Diferença observada |
|---|---|
| 2022 | Esquema-base com 125 colunas. |
| 2023 | Mesmo conjunto e mesma ordem de 125 colunas de 2022. |
| 2024 | Mantém os 125 campos-base, adiciona `COMPLICA` e termina com 17 colunas sem nome após o último campo. O inventário contabiliza 143 colunas declaradas. |
| 2025 | Mantém os 125 campos-base e adiciona `HOSPITAL`, `DDD_HOSP`, `TEL_HOSP`, `COMPLICA`, `NU_LOTE_I` e `DS_OBS`, totalizando 130 colunas. |

As colunas vazias observadas no cabeçalho de 2024 não devem ser interpretadas como variáveis válidas. Elas indicam excesso de delimitadores no cabeçalho ou uma exportação malformada e precisam ser tratadas como inconsistência estrutural.

## Tipos e domínios

Esta etapa registra o esquema e as descrições operacionais. Os tipos observados, a quantidade de vazios, os valores únicos completos e os exemplos por coluna serão calculados pelo analisador na etapa de geração do dicionário final. Em especial, códigos como `NU_NOTIFIC`, `ID_UNIDADE`, `NU_CEP` e identificadores territoriais devem ser tratados como texto durante a leitura para preservar zeros à esquerda.

Exemplos reais observados nos arquivos:

| Coluna | Exemplo |
|---|---|
| `NU_NOTIFIC` | `4645237` |
| `ID_AGRAVO` | `A92.0` |
| `DT_NOTIFIC` | `18/11/2022` |
| `CS_SEXO` | `F` |
| `NM_BAIRRO` | `ENCRUZILHADA` |
| `FEBRE` | `2` |
| `CLASSI_FIN` | `5` |

Os campos de sintomas, sinais de alarme e gravidade aparecem predominantemente codificados numericamente, mas isso não significa que sejam variáveis quantitativas: seus códigos representam categorias da ficha. Campos de data também não devem ser inferidos apenas pelo nome; os quatro arquivos precisam ser analisados para registrar o formato efetivamente encontrado.

## Observações para a consolidação

1. 2022 e 2023 podem ser agrupados quanto ao esquema de colunas.
2. 2024 deve permanecer em uma variante própria por causa das colunas sem nome e de `COMPLICA`.
3. 2025 deve permanecer em uma variante própria por causa dos seis campos adicionais.
4. A análise final deve distinguir coluna ausente, coluna vazia e coluna presente com todos os valores vazios.
5. O conteúdo de `DS_OBS`, quando presente em 2025, pode conter texto livre e caracteres afetados por problemas de encoding; ele não deve ser convertido para categoria numérica.