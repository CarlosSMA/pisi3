# Plano de implementação — previsão de carga de trabalho

## 1. Objetivo

Implementar um módulo de apoio à gestão da vigilância epidemiológica para a
Prefeitura do Recife. O sistema deve estimar a demanda administrativa futura
e ajudar o servidor a planejar revisões, encerramentos e recursos.

O sistema **não** deve diagnosticar cidadãos, prever mortes, prever gravidade
individual, afirmar onde uma doença ocorrerá, substituir decisões clínicas ou
punir unidades e servidores.

## 2. Unidade de previsão

O modelo não deve ser treinado diretamente sobre cada cidadão. A tabela
analítica deve ser agregada, com uma linha por:

```text
período futuro × unidade administrativa × agravo
```

O padrão recomendado é `semana epidemiológica × unidade de notificação ×
agravo`. Quando houver poucos registros, usar mês ou distrito e aplicar
supressão de resultados pequenos para reduzir o risco de reidentificação.

O horizonte deve ser definido pela Secretaria, por exemplo, as próximas 1 a 4
semanas. Cada previsão deve usar somente informações conhecidas até a data de
corte.

## 3. Alvos de regressão

O primeiro alvo recomendado é `novas_notificacoes`, pois pode ser construído
diretamente a partir dos CSVs tratados. Outros alvos possíveis são:

| Alvo | Definição | Uso |
|---|---|---|
| `novas_notificacoes` | Notificações no próximo período | Planejar demanda de entrada |
| `revisoes_necessarias` | Registros que exigirão correção | Dimensionar conferência |
| `pendencias_abertas` | Registros com ação administrativa pendente | Planejar a fila |
| `casos_a_encerrar` | Registros que atingirão prazo interno | Planejar encerramentos |
| `hospitalizacoes_notificadas` | Hospitalizações agregadas notificadas | Planejar demanda administrativa |

`revisoes_necessarias`, `pendencias_abertas` e `casos_a_encerrar` exigem dados
adicionais de workflow, como timestamps de atribuição, revisão, devolução e
encerramento. A hospitalização deve ser tratada apenas como volume agregado,
nunca como desfecho individual.

O modelo deve produzir uma contagem e um intervalo de previsão, por exemplo:

> 38 registros estimados, com intervalo de 25 a 54.

Antes de usar ML, comparar com baselines obrigatórios: média móvel, valor da
mesma semana anterior, sazonalidade anual e média histórica da unidade.

## 4. Alvos de classificação

A classificação deve descrever a carga do período, não classificar pessoas:

- **faixa de volume:** baixo, esperado, alto ou muito alto;
- **capacidade operacional:** dentro da capacidade, atenção ou acima da
  capacidade;
- **necessidade de reforço:** sim ou não, sempre sujeita à revisão humana;
- **desvio operacional:** normal ou atípico, comparando observado e esperado;
- **situação da fila:** normal, atenção ou atrasada, apenas para pendências
  administrativas.

As faixas devem ser definidas por limiares institucionais ou quantis históricos.
A classe “acima da capacidade” só pode ser usada se a Secretaria fornecer a
capacidade de referência de cada unidade.

Não criar categorias como “bairro perigoso”, “unidade ruim” ou “servidor
ineficiente”. A classe deve representar a carga estimada do período.

## 5. Variáveis de entrada permitidas

Usar somente dados agregados e históricos disponíveis no momento da previsão:

- contagens defasadas de notificações, revisões, pendências e encerramentos;
- médias móveis e tendências das últimas semanas ou meses;
- semana epidemiológica, mês, ano e feriados;
- agravo já informado, unidade e distrito administrativo;
- proporção histórica de registros incompletos;
- tempo operacional agregado;
- capacidade declarada da unidade;
- campanhas, mudanças de protocolo e interrupções do sistema.

Não utilizar nome, endereço, CEP, número de notificação, texto livre ou
atributos demográficos individuais. Sintomas, exames, classificação clínica
final, evolução e óbito não são necessários para esse objetivo e devem ser
excluídos.

## 6. Dados que precisam ser coletados

Além dos CSVs atuais, a Prefeitura deve registrar:

1. entrada, atribuição, revisão, devolução e encerramento de cada tarefa;
2. definição formal de registro incompleto;
3. capacidade semanal e indisponibilidade de cada unidade;
4. feriados, campanhas, alterações de protocolo e interrupções do sistema;
5. população atendida ou outro denominador, quando houver comparação
   territorial;
6. decisão humana e resultado de cada alerta.

## 7. Integração com o aplicativo mobile

O aplicativo deve mostrar:

- período e unidade da previsão;
- alvo previsto e valor estimado;
- intervalo de incerteza;
- classificação operacional;
- data de atualização e versão do modelo;
- dados considerados e explicação do alerta;
- ação sugerida;
- opções para aceitar, rejeitar ou revisar a sugestão.

O modelo não deve redistribuir tarefas automaticamente, acionar fiscalização,
comunicar cidadãos ou alterar o atendimento. O backend institucional deve
processar os dados sensíveis; o celular deve receber somente o mínimo
necessário, por conexão segura, com autenticação, autorização por função,
expiração de sessão e auditoria.

## 8. Validação

Usar validação temporal: treinar em períodos anteriores e testar em um período
posterior, simulando a operação real. Não misturar dados futuros no treinamento.

Para regressão, medir:

- MAE;
- RMSE;
- erro percentual com tratamento de contagens zero;
- cobertura dos intervalos de previsão;
- desempenho em relação aos baselines.

Para classificação, medir:

- recall da classe “acima da capacidade”;
- precisão;
- matriz de confusão;
- calibração;
- taxa de falsos alertas.

Avaliar por ano, agravo e unidade, ocultando grupos pequenos. O piloto inicial
deve operar em **modo sombra**, sem alterar a fila real, até que servidores,
área de dados, segurança e jurídico validem seu comportamento.

## 9. Governança, ética e LGPD

Dados de saúde são dados pessoais sensíveis. Antes da produção, devem ser
definidas finalidade pública, necessidade, minimização, controle de acesso,
segurança, retenção, transparência, responsável pelo modelo, procedimento de
contestação e resposta a incidentes.

O aplicativo deve exibir claramente:

> **Estimativa de apoio à gestão — não é decisão automática nem diagnóstico.**

Dados reais não devem ser usados em desenvolvimento, testes ou telemetria.
Utilizar dados sintéticos ou anonimizados, com processamento sensível no
backend institucional. Este plano não substitui análise de impacto, parecer
jurídico ou autorização do controlador dos dados.

## 10. Ordem de implementação

1. Construir a tabela agregada semanal por unidade e agravo.
2. Implementar regras de qualidade e os baselines de volume.
3. Criar o alvo `novas_notificacoes` e validar a regressão temporalmente.
4. Adicionar classificação de faixa de volume e capacidade.
5. Coletar dados de workflow para prever revisões e pendências.
6. Integrar previsões explicáveis ao mobile.
7. Executar piloto em modo sombra e auditar desempenho e impactos.
