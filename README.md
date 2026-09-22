<p align="center">
<img width="300" height="300" alt="logo-vetorrisco-redonda" src="https://github.com/user-attachments/assets/36d2433d-6925-4163-97e8-5e10e11327cc" />
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
