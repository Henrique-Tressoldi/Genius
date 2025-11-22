import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import Counter
import time
import os
import base64
from google.api_core import exceptions as ga_exceptions

# ==============================================================================
# 1. SETUP & INFRAESTRUTURA
# ==============================================================================
try: DEFAULT_KEY = st.secrets["GEMINI_KEY"]
except: DEFAULT_KEY = ""

# Configuração de Imagens
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Ifood_logo.svg/2560px-Ifood_logo.svg.png"
LOCAL_HEADER_LOGO = "ifood_Logo.png"
ICON_PATH = "ifood_icon.jpg"
ROUND_ICON = "ifood_icon_round.png"

def load_local_image(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/jpeg" if path.lower().endswith(('.jpg', '.jpeg')) else "image/png"
                return f"data:{mime};base64,{encoded}"
        except: pass
    return None

local_logo_data = load_local_image(LOCAL_HEADER_LOGO)
if local_logo_data: LOGO_URL = local_logo_data

# Favicon
if not os.path.exists(ROUND_ICON) and os.path.exists(ICON_PATH):
    try:
        from PIL import Image, ImageDraw
        img = Image.open(ICON_PATH).convert("RGBA")
        s = min(img.size)
        img = img.crop(((img.width-s)//2, (img.height-s)//2, (img.width+s)//2, (img.height+s)//2)).resize((256, 256), Image.LANCZOS)
        mask = Image.new("L", (256, 256), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 256, 256), fill=255)
        img.putalpha(mask)
        img.save(ROUND_ICON, format="PNG")
    except: pass

page_icon = ROUND_ICON if os.path.exists(ROUND_ICON) else (ICON_PATH if os.path.exists(ICON_PATH) else "🔴")

st.set_page_config(page_title="iFood Partner Portal", page_icon=page_icon, layout="wide", initial_sidebar_state="collapsed")

# --- CSS: VISUAL IFOOD PURO ---
def carregar_css():
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
        * {{ font-family: 'Nunito Sans', sans-serif !important; }}
        [data-testid="stAppViewContainer"] {{ background-color: #F7F7F7 !important; }}
        
        div[data-baseweb="select"] > div {{ background-color: #FFFFFF !important; color: #000000 !important; border-radius: 12px !important; }}
        .stTextInput > div > div > input {{ background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #E6E6E6 !important; padding: 12px 14px !important; border-radius: 12px !important; }}

        .css-card {{ background-color: #FFFFFF !important; border-radius: 16px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #F0F0F0; margin-bottom: 15px; }}
        .metric-box {{ background: #FFF; padding: 20px; border-radius: 12px; border: 1px solid #E0E0E0; text-align: center; }}
        
        .status-tag {{ padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }}
        .tag-URGENTE {{ background: #EA1D2C; color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(234, 29, 44, 0.2); }}
        .tag-MEDIA {{ background: #FEF3C7; color: #D97706 !important; }}
        .tag-BAIXA {{ background: #D1FAE5; color: #059669 !important; }}

        .stButton button {{
            background-color: #EA1D2C !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            width: 100%;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stButton button:hover {{
            background-color: #C21925 !important;
            color: white !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(234, 29, 44, 0.3) !important;
        }}
        .stButton button:active, .stButton button:focus {{
            background-color: #A3151F !important;
            color: white !important;
            border: none !important;
            box-shadow: none !important;
        }}

        header[data-testid="stHeader"], footer {{ display: none !important; }}
        .top-app-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 80px; background-color: #FFFFFF; border-bottom: 1px solid #E6E6E6; display: flex; align-items: center; justify-content: space-between; padding: 0 30px 0 370px; z-index: 999999; }}
        .main .block-container {{ padding-top: 120px !important; padding-left: 3rem !important; padding-right: 3rem !important; max-width: 100%; }}
        
        @media (max-width: 800px) {{
            .top-app-header {{ height: 70px !important; padding: 0 15px !important; flex-direction: row !important; gap: 10px !important; }}
            .header-left img {{ width: 40px !important; height: 40px !important; }}
            .header-right .loja-info {{ display: none; }}
            .main .block-container {{ padding-top: 140px !important; padding-left: 1rem !important; padding-right: 1rem !important; }}
        }}
    </style>
    <div class="top-app-header">
        <div class="header-left" style="display:flex; align-items:center; gap:12px;">
            <img src="{LOGO_URL}" style="width:48px; height:48px; border-radius:10px; object-fit:cover;"/>
            <span style="font-size:1.1rem; font-weight:700; color:#333;">Portal Parceiro</span>
        </div>
        <div class="header-right" style="display:flex; align-items:center; gap:15px;">
            <div class="loja-info" style="text-align:right; line-height:1.2;">
                <div style="font-size:14px; font-weight:700; color:#333;">Minha Loja</div>
                <div style="font-size:11px; color:#00A85A; font-weight:700;">● ABERTA</div>
            </div>
            <div style="width:40px; height:40px; background:#EA1D2C; border-radius:50%; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold;">L</div>
        </div>
    </div>
    """
st.markdown(carregar_css(), unsafe_allow_html=True)

# ==============================================================================
# 2. IA CONFIG
# ==============================================================================
@st.cache_resource
def get_model(api_key):
    if not api_key: return None, None
    try:
        genai.configure(api_key=api_key)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}
        for m in genai.list_models():
            if 'flash' in m.name.lower(): return genai.GenerativeModel(m.name), safety
        return genai.GenerativeModel('gemini-1.5-pro'), safety
    except: return None, None

model, safety = get_model(DEFAULT_KEY)

def _safe_generate(prompt):
    if not model: return "Offline."
    try: return model.generate_content(prompt, safety_settings=safety).text.strip()
    except: return "Erro na IA."

def render_phone(item, msg):
    return f"""
    <div style="border:12px solid #222; border-radius:30px; background:#fff; max-width:280px; margin:0 auto; box-shadow: 0 20px 40px rgba(0,0,0,0.2); overflow:hidden;">
        <div style="background:#EA1D2C; height:380px; padding:20px; display:flex; flex-direction:column; justify-content:center;">
            <div style="background:#fff; border-radius:12px; padding:16px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.15);">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="font-size:10px; font-weight:800; color:#444;">IFOOD • AGORA</span>
                    <span style="font-size:10px; color:#999;">1m</span>
                </div>
                <div style="font-size:13px; font-weight:800; color:#111; margin-bottom:4px;">{item} 😋</div>
                <div style="font-size:12px; color:#555; line-height:1.4;">{msg}</div>
            </div>
        </div>
    </div>"""

# ==============================================================================
# 3. FRAGMENTOS (UI MODULARIZADA)
# ==============================================================================

@st.fragment
def render_support_tab():
    count = 0
    if os.path.exists('suporte_ifood_simulado.csv'):
        df = pd.read_csv('suporte_ifood_simulado.csv')
        count = len(df)
    
    st.write("")
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.markdown(f"""<div class="css-card" style="border-left:8px solid #EA1D2C; padding:30px;">
            <div style="color:#666; font-weight:700; letter-spacing:1px;">FILA DE ATENDIMENTO</div>
            <div style="font-size:4rem; font-weight:900; color:#333; line-height:1.1;">{count}</div>
            <div style="color:#EA1D2C; font-weight:bold;">Tickets Pendentes</div></div>""", unsafe_allow_html=True)
        if st.button("⚡ TRIAGEM AUTOMÁTICA"): st.session_state['processed'] = True

    with c2:
        if st.session_state.get('processed') and count > 0:
            st.markdown("##### 📋 Análise de Risco & Churn")
            for i, row in df.head(3).iterrows():
                msg = row['mensagem_cliente']
                prompt = f"""Analise este ticket do iFood: '{msg}'. 
                1. Classifique: URGENTE, MEDIA ou BAIXA.
                2. Dê uma ação prática curta para evitar o CHURN (perda do cliente).
                3. Escreva uma resposta curta e empática para o cliente.
                Responda estritamente no formato: CLASSIFICACAO | ACAO ANTI-CHURN | RESPOSTA AO CLIENTE"""
                
                res_raw = _safe_generate(prompt)
                
                # TRATAMENTO DE ERRO DE API (OFFLINE)
                if "Offline" in res_raw or "Erro" in res_raw:
                    st.warning("⚠️ IA Offline ou Erro de Conexão. Verifique sua API Key.")
                    continue

                # Parsing Robusto
                parts = res_raw.split('|')
                if len(parts) >= 3:
                    tag_txt = parts[0].strip()
                    churn_action = parts[1].strip()
                    client_response = parts[2].strip()
                else:
                    tag_txt = "ANÁLISE"
                    churn_action = res_raw
                    client_response = "---"

                cls = "tag-URGENTE" if "URGENTE" in tag_txt.upper() else ("tag-MEDIA" if "MEDIA" in tag_txt.upper() else "tag-BAIXA")
                border_color = "#EA1D2C" if "URGENTE" in tag_txt.upper() else "#EEE"
                
                # HTML Compactado para evitar quebra de renderização
                html_content = f"""
                <div class="css-card" style="padding:20px; border-left: 5px solid {border_color}; position:relative;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                        <span style="font-weight:800; color:#333; font-size:1rem;">Ticket #{i+1}</span>
                        <span class="status-tag {cls}">{tag_txt}</span>
                    </div>
                    <div style="font-style:italic; color:#555; margin-bottom:15px;">"{msg}"</div>
                    <div style="margin-bottom:10px;">
                        <strong style="color:#EA1D2C; font-size:0.85rem;">🛡️ AÇÃO ANTI-CHURN:</strong>
                        <div style="font-size:0.9rem; color:#374151; margin-top:2px;">{churn_action}</div>
                    </div>
                    <div style="background:#F0F9FF; padding:12px; border-radius:8px; border:1px solid #E0F2FE;">
                        <strong style="color:#0284C7; font-size:0.85rem;">💬 SUGESTÃO DE RESPOSTA:</strong>
                        <div style="font-size:0.9rem; color:#374151; margin-top:2px; font-style:italic;">"{client_response}"</div>
                    </div>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)

@st.fragment
def render_sales_tab():
    st.write("")
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        itens = [x.strip() for i in df_v['itens'] for x in str(i).split('+')]
        top = Counter(itens).most_common(1)[0][0] if itens else "N/A"
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div class="metric-box"><small>FATURAMENTO</small><h3>R$ {df_v['valor_total'].sum():.2f}</h3></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-box"><small>PEDIDOS</small><h3>{len(df_v)}</h3></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-box"><small>CAMPEÃO</small><h3 style="color:#EA1D2C;">{top}</h3></div>""", unsafe_allow_html=True)
        
        st.write("")
        c_ia, c_tb = st.columns([1, 1.5])
        with c_ia:
            st.markdown(f"""<div class="css-card"><h4 style="color:#EA1D2C;">🔥 Gerador de Combos</h4><p>Crie 5 estratégias para vender mais <b>{top}</b>.</p></div>""", unsafe_allow_html=True)
            
            if st.button("✨ GERAR 5 COMBOS PROMOCIONAIS"):
                with st.spinner("Criando estratégias..."):
                    prompt = f"Crie 5 sugestões de COMBOS promocionais diferentes e criativos envolvendo {top}. Formato lista markdown simples."
                    res = _safe_generate(prompt)
                    st.success("Estratégias geradas!")
                    st.markdown(f"""<div class="css-card" style="background:#FFF5F5 !important;">{res}</div>""", unsafe_allow_html=True)
        
        with c_tb:
            st.dataframe(df_v, width=None, height=400, use_container_width=True)

@st.fragment
def render_crm_tab():
    st.write("")
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        if 'cliente' in df_v.columns:
            c_l, c_r = st.columns([1.2, 1])
            with c_l:
                st.markdown("### 🎯 Sniper CRM")
                st.markdown("Selecione um cliente para enviar uma oferta única e personalizada.")
                cli = st.selectbox("Base de Clientes:", df_v['cliente'].unique())
                itens_c = [x.strip() for i in df_v[df_v['cliente']==cli]['itens'] for x in str(i).split('+')]
                fav = Counter(itens_c).most_common(1)[0][0] if itens_c else "?"
                st.info(f"Prato favorito: **{fav}**")
                
                if st.button("🚀 DISPARAR OFERTA ÚNICA"):
                    prompt = f"Aja como iFood. Cliente: {cli}. Favorito: {fav}. Escreva 1 notificação push curta, urgente e irresistível com emoji. Texto puro apenas."
                    res = _safe_generate(prompt)
                    st.session_state['crm_push'] = {'msg': res, 'item': fav}
            
            with c_r:
                push_data = st.session_state.get('crm_push', {'msg': 'Aguardando disparo...', 'item': 'IFOOD'})
                st.markdown(render_phone(push_data['item'], push_data['msg']), unsafe_allow_html=True)

@st.fragment
def render_chat_tab():
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.markdown("""<div class="css-card"><h4 style='color:#EA1D2C; margin:0;'>Genius Assistant 💬</h4><p style='font-size:0.9rem; color:#555;'>Pergunte sobre seus dados de vendas.</p></div>""", unsafe_allow_html=True)
        
        if 'chat_history' not in st.session_state: st.session_state['chat_history'] = []

        def on_submission():
            txt = st.session_state.get("chat_input_w")
            if txt:
                st.session_state['chat_history'] = st.session_state['chat_history'] + [{'role': 'user', 'text': txt}]
                ctx = ""
                if os.path.exists('vendas_restaurante.csv'): 
                    ctx = pd.read_csv('vendas_restaurante.csv').tail(30).to_string(index=False)
                resp = _safe_generate(f"Dados: {ctx}. Pergunta: {txt}. Responda curto e com emojis.")
                st.session_state['chat_history'] = st.session_state['chat_history'] + [{'role': 'assistant', 'text': resp}]
                st.session_state.chat_input_w = ""

        def click_suggestion(sugestao):
            st.session_state.chat_input_w = sugestao 
            st.session_state['chat_history'] = st.session_state['chat_history'] + [{'role': 'user', 'text': sugestao}]
            ctx = ""
            if os.path.exists('vendas_restaurante.csv'): 
                ctx = pd.read_csv('vendas_restaurante.csv').tail(30).to_string(index=False)
            resp = _safe_generate(f"Dados: {ctx}. Pergunta: {sugestao}. Responda curto e com emojis.")
            st.session_state['chat_history'] = st.session_state['chat_history'] + [{'role': 'assistant', 'text': resp}]
            st.session_state.chat_input_w = ""

        st.text_input("Digite sua pergunta:", key="chat_input_w", on_change=on_submission)
        st.button("Enviar", on_click=on_submission)

        for msg in reversed(st.session_state['chat_history']):
            align = "right" if msg['role'] == 'user' else "left"
            bg = "#F3F4F6" if msg['role'] == 'user' else "#FFF0F0"
            color = "#333" if msg['role'] == 'user' else "#EA1D2C"
            st.markdown(f"""<div style="text-align:{align}; margin-bottom:8px;"><span style="background:{bg}; color:{color}; padding:8px 14px; border-radius:12px; display:inline-block; font-size:0.9rem; font-weight:500;">{msg['text']}</span></div>""", unsafe_allow_html=True)

    with c_right:
        st.info("💡 **Sugestões:**")
        st.button("💰 Faturamento?", on_click=click_suggestion, args=("Faturamento total?",))
        st.button("🏆 Melhor Cliente?", on_click=click_suggestion, args=("Melhor cliente?",))
        st.button("🍔 Top Produto?", on_click=click_suggestion, args=("Produto mais vendido?",))

# ==============================================================================
# 4. ORQUESTRAÇÃO
# ==============================================================================
st.write("") 
tab_sup, tab_vend, tab_crm, tab_chat = st.tabs(["🛡️ Central de Suporte", "💰 Engenharia de Vendas", "🎯 CRM Preditivo", "🤖 Genius Assistant"])

with tab_sup: render_support_tab()
with tab_vend: render_sales_tab()
with tab_crm: render_crm_tab()
with tab_chat: render_chat_tab()