import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import Counter
import time
import os
import base64
import datetime
import uuid
from google.api_core import exceptions as ga_exceptions
import logging

# ==============================================================================
# 1. CONFIGURAÇÃO INICIAL (SETUP)
# ==============================================================================

# Recupera API Key
try:
    DEFAULT_KEY = st.secrets["GEMINI_KEY"]
except:
    DEFAULT_KEY = ""

# Configuração de Imagens e Ícones
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Ifood_logo.svg/2560px-Ifood_logo.svg.png"
LOCAL_HEADER_LOGO = "ifood_Logo.png"
ICON_PATH = "ifood_icon.jpg"
ROUND_ICON = "ifood_icon_round.png"

# Tenta carregar logo local em Base64 para não depender de link externo
if os.path.exists(LOCAL_HEADER_LOGO):
    try:
        with open(LOCAL_HEADER_LOGO, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png"
            if LOCAL_HEADER_LOGO.lower().endswith(".jpg"): mime = "image/jpeg"
            LOGO_URL = f"data:{mime};base64,{encoded}"
    except Exception:
        pass

# Gera favicon redondo se necessário
def _try_generate_round_icon(src, out):
    try:
        from PIL import Image, ImageDraw
        if not os.path.exists(out) and os.path.exists(src):
            img = Image.open(src).convert("RGBA")
            s = min(img.size)
            img = img.crop(((img.width-s)//2, (img.height-s)//2, (img.width+s)//2, (img.height+s)//2)).resize((256, 256), Image.LANCZOS)
            mask = Image.new("L", (256, 256), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 256, 256), fill=255)
            img.putalpha(mask)
            img.save(out, format="PNG")
    except: pass

_try_generate_round_icon(ICON_PATH, ROUND_ICON)
page_icon = ROUND_ICON if os.path.exists(ROUND_ICON) else (ICON_PATH if os.path.exists(ICON_PATH) else "🔴")

st.set_page_config(
    page_title="iFood Partner Portal",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar fechada para dar foco no mobile
)

# ==============================================================================
# 2. CSS CRÍTICO (CORREÇÃO DE LAYOUT)
# ==============================================================================
def carregar_css():
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
        * {{ font-family: 'Nunito Sans', sans-serif !important; }}
        
        /* --- CORREÇÃO DE ESTRUTURA (O PONTO DE FALHA ANTERIOR) --- */
        [data-testid="stAppViewContainer"] {{ background-color: #F7F7F7 !important; }}
        
        /* Padding Desktop: Empurra o conteúdo para baixo do header de 80px */
        .main .block-container {{ 
            padding-top: 120px !important; 
            padding-left: 3rem !important; 
            padding-right: 3rem !important; 
            max-width: 100%; 
        }}

        /* --- HEADER FIXO --- */
        .top-app-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 80px;
            background-color: #FFFFFF;
            border-bottom: 1px solid #E6E6E6;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 40px;
            z-index: 999999; /* Acima de tudo */
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        }}

        /* --- CSS MOBILE (A SOLUÇÃO DO PROBLEMA) --- */
        @media (max-width: 800px) {{
            /* Header Mobile: Mais compacto e garantido na horizontal */
            .top-app-header {{
                height: 70px !important;
                padding: 0 15px !important;
                flex-wrap: nowrap !important; /* Impede quebra de linha */
            }}
            .header-left img {{ width: 40px !important; height: 40px !important; }}
            .header-left span {{ font-size: 1rem !important; }}
            .header-right .loja-info {{ display: none !important; }} /* Esconde info extra para caber */
            
            /* PADDING MASSIVO: Empurra o conteúdo (abas) para longe do header */
            .main .block-container {{ 
                padding-top: 140px !important; /* Buffer de segurança */
                padding-left: 1rem !important; 
                padding-right: 1rem !important; 
            }}
        }}

        /* --- COMPONENTES VISUAIS --- */
        .css-card {{ background-color: #FFFFFF !important; border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #EEE; margin-bottom: 20px; }}
        .metric-box {{ background: #FFF; padding: 20px; border-radius: 12px; border: 1px solid #E0E0E0; text-align: center; }}
        .ai-result-box {{ background-color: #F0FDF4 !important; border: 1px solid #BBF7D0 !important; border-radius: 12px; padding: 20px; margin-top: 15px; color: #14532D !important; }}
        
        /* Botões */
        .stButton button {{ background-color: #EA1D2C !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; width: 100%; }}
        
        /* Inputs */
        .stTextInput > div > div > input {{
            border-radius: 12px !important;
            padding: 12px !important;
            border: 1px solid #DDD !important;
        }}

        /* Tags */
        .status-tag {{ padding: 6px 14px; border-radius: 100px; font-size: 11px; font-weight: 800; text-transform: uppercase; }}
        .tag-URGENTE {{ background: #FEE2E2; color: #DC2626; }}
        .tag-MEDIA {{ background: #FEF3C7; color: #D97706; }}
        .tag-BAIXA {{ background: #D1FAE5; color: #059669; }}
        
        /* Esconde elementos nativos */
        header[data-testid="stHeader"], footer, #MainMenu {{ display: none !important; }}
    </style>

    <div class="top-app-header">
        <div class="header-left" style="display:flex; align-items:center; gap:12px;">
            <img src="{LOGO_URL}" style="width:48px; height:48px; border-radius:8px; object-fit:cover;" alt="Logo"/>
            <span style="font-size:1.2rem; font-weight:700; color:#333;">Parceiro</span>
        </div>
        <div class="header-right" style="display:flex; align-items:center; gap:15px;">
            <div class="loja-info" style="text-align:right;">
                <div style="font-size:14px; font-weight:700; color:#333;">Minha Loja</div>
                <div style="font-size:11px; color:#00A85A; font-weight:700;">● ONLINE</div>
            </div>
            <div style="width:40px; height:40px; background:#EA1D2C; border-radius:50%; color:white; display:flex; align-items:center; justify-content:center; font-weight:800;">L</div>
        </div>
    </div>
    """
st.markdown(carregar_css(), unsafe_allow_html=True)

# ==============================================================================
# 3. LÓGICA DE NEGÓCIO (BACKEND)
# ==============================================================================

# Função de Rerun Robusta (Compatível com vnova e velha)
def force_reload():
    if hasattr(st, "rerun"): st.rerun()
    elif hasattr(st, "experimental_rerun"): st.experimental_rerun()
    else: st.exception("Por favor atualize o Streamlit.")

# Configura IA
@st.cache_resource
def get_model(key):
    if not key: return None
    genai.configure(api_key=key)
    safe = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}
    # Tenta usar modelo rápido (Flash)
    for m in genai.list_models():
        if 'flash' in m.name.lower(): return genai.GenerativeModel(m.name), safe
    return genai.GenerativeModel('gemini-1.5-pro'), safe

model, safety = get_model(DEFAULT_KEY)

def ask_ai(prompt):
    if not model: return "⚠️ Genius Offline (Sem API Key)"
    try:
        return model.generate_content(prompt, safety_settings=safety).text.strip()
    except Exception as e: return f"Erro: {str(e)[:50]}"

# ==============================================================================
# 4. INTERFACE PRINCIPAL
# ==============================================================================

# Abas de Navegação
tab1, tab2, tab3, tab4 = st.tabs(["🛡️ Suporte", "💰 Vendas", "🎯 CRM", "🤖 Genius"])

# --- ABA 1: SUPORTE ---
with tab1:
    if os.path.exists('suporte_ifood_simulado.csv'):
        df_sup = pd.read_csv('suporte_ifood_simulado.csv')
        pendentes = len(df_sup)
    else:
        df_sup = pd.DataFrame()
        pendentes = 0
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div class="css-card" style="border-left: 6px solid #EA1D2C;">
            <div style="color:#666; font-size:0.9rem; font-weight:700;">FILA ATUAL</div>
            <div style="font-size:3.5rem; font-weight:800; color:#333; line-height:1;">{pendentes}</div>
            <div style="color:#EA1D2C; font-weight:bold;">Tickets</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ TRIAGEM COM IA"):
            st.session_state['triagem_active'] = True
            force_reload()

    with c2:
        if st.session_state.get('triagem_active') and not df_sup.empty:
            for i, row in df_sup.head(3).iterrows():
                msg = row.get('mensagem_cliente', '')
                res = ask_ai(f"Classifique (URGENTE/MEDIA/BAIXA) e resuma em 5 palavras: '{msg}'")
                
                tag_cls = "tag-BAIXA"
                if "URGENTE" in res.upper(): tag_cls = "tag-URGENTE"
                elif "MEDIA" in res.upper(): tag_cls = "tag-MEDIA"
                
                st.markdown(f"""
                <div class="css-card" style="padding:15px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:800; color:#555;">TICKET #{i+1}</span>
                        <span class="status-tag {tag_cls}">{res.split()[0]}</span>
                    </div>
                    <div style="margin:8px 0; color:#333;">"{msg}"</div>
                    <div style="background:#F9F9F9; padding:8px; border-radius:6px; font-size:0.85rem; color:#666;">
                        🤖 {res}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- ABA 2: VENDAS ---
with tab2:
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        total = df_v['valor_total'].sum()
        
        itens = []
        for x in df_v['itens']: itens.extend(str(x).split('+'))
        top_item = Counter([i.strip() for i in itens]).most_common(1)[0][0]
        
        m1, m2 = st.columns(2)
        m1.markdown(f"""<div class="metric-box"><div>FATURAMENTO</div><h2 style="margin:0; color:#333;">R$ {total:.2f}</h2></div>""", unsafe_allow_html=True)
        m2.markdown(f"""<div class="metric-box"><div>CAMPEÃO</div><h2 style="margin:0; color:#EA1D2C;">{top_item}</h2></div>""", unsafe_allow_html=True)
        
        st.write("")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
        
        if st.button("💡 PEDIR DICA DE VENDA PARA IA"):
            dica = ask_ai(f"Dê uma ideia de promoção curta para vender mais {top_item}. Use emoji.")
            st.success(dica)

# --- ABA 3: CRM ---
with tab3:
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        clientes = df_v['cliente'].unique()
        sel_cli = st.selectbox("Escolha o Cliente:", clientes)
        
        # Analisa cliente
        hist = df_v[df_v['cliente'] == sel_cli]
        itens_cli = []
        for x in hist['itens']: itens_cli.extend(str(x).split('+'))
        fav = Counter([i.strip() for i in itens_cli]).most_common(1)[0][0]
        
        st.info(f"O prato favorito de **{sel_cli}** é **{fav}**.")
        
        if st.button("📲 GERAR NOTIFICAÇÃO PUSH"):
            push = ask_ai(f"Crie notificação push curta (max 10 palavras) para {sel_cli} comprar {fav} agora. Urgente e com emoji.")
            st.markdown(f"""
            <div style="max-width:300px; margin:20px auto; border:12px solid #333; border-radius:30px; overflow:hidden;">
                <div style="background:#EA1D2C; padding:40px 20px; color:white; min-height:300px;">
                    <div style="background:white; color:black; padding:15px; border-radius:10px; box-shadow:0 5px 15px rgba(0,0,0,0.2);">
                        <div style="font-size:10px; font-weight:bold; color:#888;">IFOOD • AGORA</div>
                        <div style="font-weight:bold; margin-top:5px;">{fav} te espera! 😋</div>
                        <div style="font-size:13px; margin-top:2px;">{push}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- ABA 4: GENIUS (CHAT) ---
with tab4:
    # 1. Inicializa Histórico
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # 2. Renderiza Mensagens (Invertido: Mais recente no topo)
    # Mostramos o histórico ANTES do input para dar contexto visual imediato ao carregar
    history_container = st.container()

    # 3. Área de Input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Pergunte ao Genius:", placeholder="Ex: Qual o dia mais fraco?")
        submit_btn = st.form_submit_button("Enviar")

    # 4. Processamento IMEDIATO (Correção do Bug de Latência)
    if submit_btn and user_input:
        # Adiciona pergunta
        st.session_state["chat_history"].append({"role": "user", "text": user_input})
        
        # Gera resposta
        ctx = ""
        if os.path.exists('vendas_restaurante.csv'):
            ctx = pd.read_csv('vendas_restaurante.csv').tail(20).to_string()
        
        resposta = ask_ai(f"Dados: {ctx}. Pergunta: {user_input}. Responda curto.")
        st.session_state["chat_history"].append({"role": "bot", "text": resposta})
        
        # O SEGRED0: FORÇA O RELOAD AGORA
        force_reload()

    # 5. Preenche o container de histórico (Visualização)
    with history_container:
        if not st.session_state["chat_history"]:
            st.markdown("""
            <div style="text-align:center; padding:40px; color:#999;">
                👋 <strong>Olá!</strong> Eu sou o Genius.<br>Analiso seus dados em segundos.
            </div>
            """, unsafe_allow_html=True)
        
        # Loop reverso para mensagens mais novas em cima (estilo timeline)
        for msg in reversed(st.session_state["chat_history"]):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="text-align:right; margin-bottom:10px;">
                    <span style="background:#E5E7EB; color:#333; padding:8px 16px; border-radius:20px 20px 0 20px; display:inline-block; font-size:0.9rem;">
                        {msg['text']}
                    </span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align:left; margin-bottom:20px;">
                    <span style="background:#FEF2F2; color:#B91C1C; border:1px solid #FECACA; padding:10px 16px; border-radius:20px 20px 20px 0; display:inline-block; font-size:0.9rem;">
                        🤖 <strong>Genius:</strong> {msg['text']}
                    </span>
                </div>""", unsafe_allow_html=True)