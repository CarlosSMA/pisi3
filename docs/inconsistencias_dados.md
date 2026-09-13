# Inconsistências e qualidade dos dados CSV

## Escopo da análise

Esta etapa analisa os 12 arquivos CSV sem modificar os dados originais. Foram observados 35.990 registros e 4.597.713 células de dados. Os percentuais de vazios abaixo representam células vazias em relação ao total de células do arquivo, não registros inteiramente vazios.

## Resumo dos achados

| Categoria | Achado |
|---|---|
| Separador | Todos os arquivos usam `;`. |
| Encoding | Todos foram lidos como UTF-8 com BOM (`utf-8-sig`), mas há caracteres textuais corrompidos em alguns valores. |
| Valores vazios | Variam de 23,48% a 61,21% das células, conforme doença e ano. |
| Datas | Há formatos `d/m/aaaa`, `dd/mm/aaaa`, `aaaa-mm-dd` e números de cinco dígitos com aparência de serial Excel. |
| Decimais indevidos | Arquivos de 2023 contêm códigos como `2.0`, `2023.0`, `26.0` e `261160.0`. |
| Sentinelas | Foram observados `0`, `9` e `XXX`; seus significados dependem do campo. |
| Encoding textual | Foram encontrados sinais como `µ`, `€`, `░` e bytes de controle em textos livres ou endereços. |
| Largura das linhas | O inventário inicial não encontrou linhas com quantidade de campos diferente do cabeçalho. Isso não elimina cabeçalhos semanticamente incorretos. |

## Vazios por arquivo

| Arquivo | Registros | Células vazias | Percentual de células vazias |
|---|---:|---:|---:|
| `chikungunya-2022.csv` | 2.110 | 141.946 | 53,82% |
| `chikungunya-2023.csv` | 1.555 | 106.774 | 54,93% |
| `chikungunya-2024.csv` | 2.481 | 217.159 | 61,21% |
| `chikungunya-2025.csv` | 1.942 | 145.739 | 57,73% |
| `dengue-2022.csv` | 2.906 | 213.027 | 56,39% |
| `dengue-2023.csv` | 3.523 | 262.748 | 57,37% |
| `dengue-2024.csv` | 10.548 | 794.325 | 57,93% |
| `dengue-2025.csv` | 9.187 | 688.208 | 57,62% |
| `zika-2022.csv` | 216 | 2.384 | 23,48% |
| `zika-2023.csv` | 226 | 2.499 | 23,53% |
| `zika-2024.csv` | 475 | 6.179 | 27,68% |
| `zika-2025.csv` | 821 | 10.854 | 28,13% |

Vazio não significa necessariamente erro. Em campos de exame, óbito, internação, complicação ou observação, a ausência pode indicar que a situação não ocorreu ou não foi informada. A análise final deve distinguir pelo menos: string vazia, campo não aplicável, código ignorado e valor ausente por falha de preenchimento.

## Formatos de data

Foram encontrados os seguintes padrões de representação:

| Padrão | Exemplos | Arquivos observados |
|---|---|---|
| Dia/mês/ano sem zero à esquerda | `19/1/2022`, `6/1/2022` | Chikungunya 2022/2023, Zika 2022/2023/2025 e Dengue 2023 em pequena quantidade. |
| Dia/mês/ano com dois dígitos | `04/04/2025`, `08/01/2025` | Chikungunya 2025, Dengue 2024/2025 e Zika 2025. |
| ISO | `2024-02-28`, `2024-01-02` | Chikungunya 2024, Dengue 2022/2023 e Zika 2024. |
| Número de cinco dígitos | `45363`, `45658`, `45720` | Chikungunya 2025 e Dengue 2024/2025, entre outros campos numéricos. |

Os números de cinco dígitos podem ser datas serializadas pelo Excel, mas também podem ser códigos ou identificadores. A conversão deve ocorrer somente quando a coluna for conhecida como data e o valor passar por validação de intervalo. Não converter todos os números automaticamente.

## Tipos mistos e decimais

Foram observados valores com sufixo `.0` em colunas que representam códigos, semanas, anos, municípios, unidades de saúde e categorias. Exemplos reais incluem:

| Valor | Risco |
|---|---|
| `2.0` | Código categórico lido como decimal. |
| `2023.0` | Ano ou código de ano lido como decimal. |
| `26.0` | Código de UF lido como decimal. |
| `261160.0` | Código de município lido como decimal. |
| `1497.0` | Código de regional lido como decimal. |

Esses valores não devem ser arredondados sem preservar o valor original. Para o dicionário, o tipo conceitual deve considerar o significado do campo: códigos e categorias são texto/categórico, mesmo quando o arquivo contém apenas dígitos.

## Valores sentinela e códigos especiais

No conjunto analisado foram contabilizadas ocorrências de `0`, `9` e `XXX`:

| Valor | Ocorrências aproximadas | Interpretação recomendada |
|---|---:|---|
| `0` | 4.481 | Pode indicar não, ausência, não ocorrência ou código específico da ficha. Interpretar por coluna. |
| `9` | 36.098 | Frequentemente representa ignorado, mas não deve ser generalizado para todos os campos. |
| `XXX` | 71 | Código ou preenchimento especial observado em campos de investigação/ocupação; exige validação por coluna. |

Os códigos `0`, `1`, `2`, `4`, `5`, `6`, `9` e `10` aparecem em sinais, sintomas, classificação e perfil. Eles são categorias da ficha, não medidas quantitativas. O dicionário final deve listar os valores observados por coluna e, quando disponível, associá-los ao domínio oficial dos JSONs de referência.

## Encoding e caracteres suspeitos

Foram encontrados aproximadamente 1.631 valores contendo caracteres suspeitos, com exemplos como:

- `2░ TRAVESSA MACAUBAL`;
- `FEITO TESTE RµPIDO`;
- `RUA PIRAUµ`;
- `REQUISI€ÇO`;
- `NÇO` e `DEFINI€ÇO`.

Esses sinais indicam que parte do texto pode ter sido exportada com uma tabela de caracteres incompatível ou sofrer corrupção anterior à geração do CSV. Embora o arquivo seja decodificável como UTF-8 com BOM, isso não garante que todos os caracteres originais estejam íntegros.

Não corrigir automaticamente esses textos no dicionário. Deve-se preservar o exemplo original, marcar a ocorrência e, se uma limpeza for necessária, manter uma versão transformada separada da fonte.

## Campos e situações que merecem atenção

1. Identificadores como `NU_NOTIFIC`, `ID_UNIDADE`, `NU_CEP`, `ID_MUNICIP` e códigos territoriais devem ser lidos como texto para preservar zeros à esquerda.
2. Datas devem ser analisadas por coluna, pois o mesmo arquivo pode misturar datas válidas, vazios e números serializados.
3. `DS_OBS` contém texto livre e pode concentrar caracteres corrompidos, mensagens administrativas e informações clínicas.
4. Os 17 cabeçalhos vazios de Chikungunya 2024 são uma inconsistência estrutural independente dos valores nulos das linhas.
5. `CS_ZONA` e `DS_OBS` não devem ser alinhados ou substituídos automaticamente.
6. Valores `9`, `0`, `99`, `999` e `XXX` precisam ser interpretados conforme o domínio de cada coluna.
7. Códigos com aparência decimal não devem ser tratados como números contínuos.

## Recomendações de tratamento

- Manter os CSVs originais sem sobrescrita.
- Ler todas as colunas como texto durante a auditoria inicial.
- Registrar formato, contagem e percentual de vazios por arquivo e coluna.
- Detectar datas por coluna, preservando o formato original no relatório.
- Separar `ausente`, `ignorado`, `não se aplica` e `não informado` quando o domínio permitir.
- Preservar códigos com zeros à esquerda.
- Registrar valores sentinela sem convertê-los silenciosamente em nulos.
- Criar uma etapa de normalização reproduzível somente depois da auditoria.
- Manter exemplos originais e exemplos normalizados lado a lado quando houver correção autorizada de encoding.