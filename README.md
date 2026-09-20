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
