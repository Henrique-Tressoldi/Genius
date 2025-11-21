import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import Counter
import os
import sys
import streamlit as st

# ==============================================================================
# ⚠️ CONFIGURAÇÃO: SUA CHAVE DE API
# ==============================================================================
# Tenta pegar dos segredos do Streamlit, ou usa vazio se não achar
try:
    MINHA_API_KEY = st.secrets["GEMINI_KEY"]
except:
    MINHA_API_KEY = ""

# ==============================================================================
# CONFIGURAÇÃO DA IA (RAW SPEED)
# ==============================================================================
def configurar_ia():
    try:
        genai.configure(api_key=MINHA_API_KEY)
        print("🔍 Buscando modelo 'Flash'...")
        
        # Segurança ZERADA
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        for m in genai.list_models():
            if 'flash' in m.name.lower() and 'exp' not in m.name.lower():
                return genai.GenerativeModel(m.name), safety_settings
                
        return genai.GenerativeModel('gemini-1.5-pro'), safety_settings
    except Exception as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
        return None, None

# --- FUNÇÃO DE GERAÇÃO DIRETA ---
def gerar_sem_limites(model, prompt, safety_settings):
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if response.candidates and response.candidates[0].content.parts:
            return response.text.strip()
        return None
    except Exception as e:
        return f"⚠️ Erro: {str(e)[:50]}..."

# ==============================================================================
# MÓDULO 1: SUPORTE
# ==============================================================================
def executar_suporte(model, safety_settings):
    print("\n" + "="*60)
    print("🤖 MÓDULO 1: SUPORTE (Velocidade da Luz)")
    print("="*60)
    
    if not os.path.exists('suporte_ifood_simulado.csv'):
        print("❌ ERRO: CSV não encontrado.")
        return

    try:
        df = pd.read_csv('suporte_ifood_simulado.csv', quotechar='"')
    except Exception as e:
        print(f"❌ Erro CSV: {e}")
        return

    for i, row in df.head(5).iterrows():
        msg = row['mensagem_cliente']
        msg_display = str(msg).replace('\n', ' ')[:60]
        
        print(f"📩 Ticket #{row.get('id_ticket', i)}: {msg_display}...")
        
        if model:
            # Prompt ajustado para ser mais direto
            prompt = f"Classifique este ticket (URGENTE/MEDIA/BAIXA) e dê justificativa técnica de 1 linha: '{msg}'"
            res = gerar_sem_limites(model, prompt, safety_settings)
            print(f"🧠 Genius: {res}")
        else:
            print("🧠 Genius: [Offline]")
        
        print("-" * 40)

# ==============================================================================
# MÓDULO 2: VENDAS GERAIS
# ==============================================================================
def executar_vendas_gerais(model):
    print("\n" + "="*60)
    print("💰 MÓDULO 2: ANÁLISE DE VENDAS")
    print("="*60)
    
    if not os.path.exists('vendas_restaurante.csv'): return

    try:
        df = pd.read_csv('vendas_restaurante.csv')
        lista_itens = []
        for i in df['itens']:
            lista_itens.extend([x.strip() for x in str(i).split('+')])
        
        if not lista_itens: return

        campeao = Counter(lista_itens).most_common(1)[0][0]
        print(f"📊 Item âncora identificado: {campeao.upper()}")
        
    except Exception as e:
        print(f"❌ Erro vendas: {e}")

# ==============================================================================
# MÓDULO 3: CRM PREDITIVO (SNIPER MODE)
# ==============================================================================
def executar_crm_sniper(model, safety_settings):
    print("\n" + "="*60)
    print("🎯 MÓDULO 3: CRM PREDITIVO (Disparo Único)")
    print("="*60)
    
    try:
        df = pd.read_csv('vendas_restaurante.csv')
        if 'cliente' not in df.columns:
            print("⚠️ Adicione coluna 'cliente' ao CSV.")
            return

        clientes_unicos = df['cliente'].unique()
        print(f"🚀 Disparando para {len(clientes_unicos)} perfis...")

        for nome_cliente in clientes_unicos:
            historico = df[df['cliente'] == nome_cliente]
            itens_cliente = []
            for i in historico['itens']:
                itens_cliente.extend([x.strip() for x in str(i).split('+')])
            
            if not itens_cliente: continue

            favorito = Counter(itens_cliente).most_common(1)[0][0]
            
            if model:
                # AQUI ESTÁ A MUDANÇA: PROMPT RESTRITIVO
                prompt = f"""
                Aja como o App do iFood.
                O cliente {nome_cliente} ama {favorito}.
                Escreva UMA ÚNICA notificação push para enviar agora.
                Regras:
                1. Sem listas (não dê opções).
                2. Sem introdução (não diga "Aqui está").
                3. Curto, urgente e com emoji.
                4. Texto final apenas.
                """
                res = gerar_sem_limites(model, prompt, safety_settings)
                print(f"📱 PUSH ({nome_cliente}): {res}")
            

    except Exception as e:
        print(f"❌ Erro CRM: {e}")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    print("🚀 INICIANDO ENGINE v17.0 (Sniper Mode)")
    
    modelo, seguranca = configurar_ia()
    
    if modelo:
        executar_suporte(modelo, seguranca)
        executar_vendas_gerais(modelo)
        executar_crm_sniper(modelo, seguranca)
        
        print("\n✅ FINALIZADO.")
    else:
        print("❌ SISTEMA PAROU.")