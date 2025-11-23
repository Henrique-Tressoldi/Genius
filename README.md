# 🚀 iFood Genius: AI Partner Portal

> **Uma Engine de Inteligência Artificial que atua como "Gerente Virtual" para parceiros iFood, transformando dados brutos em Retenção e Receita.**

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Streamlit](https://img.shields.io/badge/Frontend-Pixel%20Perfect-red) ![AI](https://img.shields.io/badge/AI-Google%20Gemini-green) ![Status](https://img.shields.io/badge/Status-MVP%20Validado-success)

---

## 💼 O Business Case (Visão de Dono)
Este projeto não é apenas um exercício de codificação; é uma **resposta estratégica** a dores reais do ecossistema de delivery.

Analisando a jornada do parceiro, identifiquei que restaurantes perdem dinheiro (ROI) por dois motivos principais:
1.  **Ineficiência Operacional (Churn):** Demora na triagem de tickets críticos (ex: comida fria/revirada) gera cancelamentos e perda de reputação.
2.  **Falta de Personalização (Ticket Médio):** Ofertas genéricas ("spray and pray") têm baixa conversão. O parceiro precisa vender o item certo para o cliente certo.

O **iFood Genius** resolve isso automatizando a tomada de decisão com GenAI.

---

## 🛠️ A Solução: 4 Pilares de Valor

### 1. 🛡️ Suporte Inteligente (SLA & Retenção)
Automatiza a triagem do SAC.
* **O que faz:** A IA lê tickets em tempo real, analisa o sentimento e classifica a urgência.
* **Impacto:** Reduz o tempo de resposta para problemas críticos (Risco Sanitário/Cancelamento), protegendo o NPS da loja.

### 2. 💰 Engenharia de Cardápio (Upsell)
Aplica o Princípio de Pareto (80/20) aos dados de vendas.
* **O que faz:** Identifica automaticamente o "Item Âncora" (mais vendido) e gera estratégias de combos com copywriting persuasivo.
* **Impacto:** Aumenta o Ticket Médio aproveitando o tráfego de itens populares.

### 3. 🎯 CRM Preditivo (Hiper-Personalização)
Sai do marketing de massa para o marketing 1:1.
* **O que faz:** Analisa o histórico individual de cada cliente (ex: "O João ama Hamburguer, a Maria ama Pizza") e gera Push Notifications únicas.
* **Impacto:** Aumenta a taxa de recompra e fidelidade (LTV).

### 4. 🤖 Genius Assistant (Chat with Data)
Democratização de dados (Data Literacy).
* **O que faz:** Um chat RAG (Retrieval-Augmented Generation) onde o dono do restaurante pode conversar com seus dados. Ex: *"Qual foi meu faturamento hoje?"*.

---

## 🧠 Engenharia & Arquitetura
Desenvolvido em **6 horas de execução focada** (Speed of Execution), priorizando robustez e escalabilidade.

### Destaques Técnicos:
* **Smart Model Selection:** O sistema implementa uma lógica de fallback que escolhe dinamicamente entre modelos (Gemini Flash para velocidade/custo vs. Pro para complexidade).
* **Resiliência (Anti-Crash):** Implementação de tratamento de erros e validação de respostas da API para garantir que o painel nunca quebre em produção.
* **Pixel Perfect UI:** Interface desenvolvida em Streamlit com injeção de CSS avançado para replicar fielmente a identidade visual (Design System) do iFood, garantindo familiaridade para o usuário.
* **Data-Driven:** Integração nativa com Pandas para processamento de CSVs e análise exploratória de dados (EDA) em tempo real.

---

## 🚀 Como Rodar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/ifood-genai-genius.git](https://github.com/SEU-USUARIO/ifood-genai-genius.git)
    ```
2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execute a aplicação:**
    ```bash
    streamlit run streamlit_app.py
    ```

---

### 👨‍💻 Sobre o Projeto
Desenvolvido por **Henrique Tressoldi** como prova de conceito para o **Programa de Estágio GenAI do iFood**.

* **Foco:** Resolução de Problemas Reais, Agilidade de Aprendizado e Entrega de Valor.
* **Stack:** Python, Streamlit, Google Gemini API, Pandas, Git.

> *"Done is better than perfect. But perfect execution of the right idea is game-changing."*
