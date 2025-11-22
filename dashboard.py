import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import Counter
import time
import os
import base64
import uuid
from google.api_core import exceptions as ga_exceptions
import logging

# ==============================================================================
# 1. SETUP & INFRAESTRUTURA
# ==============================================================================
try: DEFAULT_KEY = st.secrets["GEMINI_KEY"]
except: DEFAULT_KEY = ""

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Ifood_logo.svg/2560px-Ifood_logo.svg.png"
LOCAL_HEADER_LOGO = "ifood_Logo.png"
ICON_PATH = "ifood_icon.jpg"
ROUND_ICON = "ifood_icon_round.png"

# Carregamento de assets
if os.path.exists(LOCAL_HEADER_LOGO):
    try:
        with open(LOCAL_HEADER_LOGO, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png"
            if LOCAL_HEADER_LOGO.lower().endswith(".jpg"): mime = "image/jpeg"
            LOGO_URL = f"data:{mime};base64,{encoded}"
    except Exception: pass

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
    initial_sidebar_state="collapsed"
)

# --- CSS: LAYOUT E RESPONSIVIDADE ---
def carregar_css():
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
        * {{ font-family: 'Nunito Sans', sans-serif !important; }}
        
        [data-testid="stAppViewContainer"] {{ background-color: #F7F7F7 !important; }}
        
        /* UI Overrides */
        div[data-baseweb="select"] > div {{ background-color: #FFFFFF !important; color: #000000 !important; }}
        .css-card {{ background-color: #FFFFFF !important; border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #EEE; margin-bottom: 20px; }}
        .metric-box {{ background: #FFF; padding: 20px; border-radius: 12px; border: 1px solid #E0E0E0; text-align: center; }}
        .ai-result-box {{ background-color: #F0FDF4 !important; border: 1px solid #BBF7D0 !important; border-radius: 12px; padding: 20px; margin-top: 15px; color: #14532D !important; }}
        .stButton button {{ background-color: #EA1D2C !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; width: 100%; }}
        
        /* Remove headers padrão */
        header[data-testid="stHeader"], footer, #MainMenu {{ display: none !important; }}

        /* Estilo Inputs */
        .stTextInput > div > div > input {{
            background-color: #ffffff !important; color: #0f172a !important;
            border: 1px solid #E6E6E6 !important; padding: 12px 14px !important; border-radius: 12px !important;
        }}

        /* --- HEADER FIXO --- */
        .top-app-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 80px;
            background-color: #FFFFFF; border-bottom: 1px solid #E6E6E6;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 30px 0 370px; z-index: 999999;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        }}

        /* --- MOBILE LAYOUT FIX --- */
        /* Desktop */
        .main .block-container {{ 
            padding-top: 120px !important; padding-left: 3rem !important; padding-right: 3rem !important; max-width: 100%; 
        }}

        /* Mobile */
        @media (max-width: 800px) {{
            .top-app-header {{
                height: 70px !important; padding: 0 15px !important;
                flex-direction: row !important; flex-wrap: nowrap !important; gap: 10px !important;
            }}
            .header-left img {{ width: 40px !important; height: 40px !important; }}
            .header-left span {{ font-size: 1rem !important; }}
            .header-right .loja-info {{ display: none; }}
            
            /* Padding crítico para abas */
            .main .block-container {{ 
                padding-top: 140px !important; padding-left: 1rem !important; padding-right: 1rem !important; 
            }}
            .css-card {{ padding: 16px !important; }}
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
# 2. IA HELPER
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
    <div style="border:12px solid #222; border-radius:30px; background:#fff; max-width:280px; margin:0 auto; overflow:hidden;">
        <div style="background:#EA1D2C; height:400px; padding:20px; display:flex; align-items:center;">
            <div style="background:#fff; border-radius:10px; padding:15px; width:100%; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
                <div style="font-size:10px; font-weight:bold; color:#888;">IFOOD • AGORA</div>
                <div style="font-weight:bold; margin:5px 0;">{item} 😋</div>
                <div style="font-size:12px;">{msg}</div>
            </div>
        </div>
    </div>"""

# ==============================================================================
# 3. FRAGMENTOS DE UI (ISOLAMENTO DE ESTADO)
# ==============================================================================

# --- FRAGMENTO: SUPORTE ---
@st.fragment
def render_support_tab():
    if os.path.exists('suporte_ifood_simulado.csv'):
        df = pd.read_csv('suporte_ifood_simulado.csv')
        count = len(df)
    else: count = 0
    
    st.write("")
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.markdown(f"""<div class="css-card" style="border-left:8px solid #EA1D2C;">
            <div style="color:#666; font-weight:700;">FILA</div>
            <div style="font-size:3.5rem; font-weight:800; color:#333;">{count}</div>
            <div style="color:#EA1D2C; font-weight:bold;">Tickets</div></div>""", unsafe_allow_html=True)
        
        # O clique aqui atualiza APENAS este fragmento, mantendo a aba ativa
        if st.button("⚡ TRIAGEM"): st.session_state['processed'] = True

    with c2:
        if st.session_state.get('processed') and count > 0:
            st.markdown("##### 📋 Análise")
            for i, row in df.head(3).iterrows():
                msg = row['mensagem_cliente']
                res = _safe_generate(f"Classifique (URGENTE/MEDIA/BAIXA) e resuma: '{msg}'")
                cls = "tag-URGENTE" if "URGENTE" in res.upper() else "tag-BAIXA"
                st.markdown(f"""<div class="css-card" style="padding:15px; margin-bottom:10px;">
                    <span class="status-tag {cls}">Ticket #{i+1}</span>
                    <div style="margin:8px 0; font-weight:600;">"{msg}"</div>
                    <div style="color:#666; font-size:0.9rem;">🤖 {res}</div></div>""", unsafe_allow_html=True)

# --- FRAGMENTO: VENDAS ---
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
        c_ia, c_tb = st.columns([1, 2])
        with c_ia:
            # Clique aqui atualiza apenas o fragmento de vendas
            if st.button("✨ CRIAR OFERTA"):
                res = _safe_generate(f"Crie oferta curta para {top}. Sem titulos.")
                st.markdown(f"""<div class="ai-result-box">{res}</div>""", unsafe_allow_html=True)
        with c_tb:
            st.dataframe(df_v, width=None, height=400, use_container_width=True)

# --- FRAGMENTO: CRM ---
@st.fragment
def render_crm_tab():
    st.write("")
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        if 'cliente' in df_v.columns:
            cli = st.selectbox("Cliente:", df_v['cliente'].unique())
            itens_c = [x.strip() for i in df_v[df_v['cliente']==cli]['itens'] for x in str(i).split('+')]
            fav = Counter(itens_c).most_common(1)[0][0] if itens_c else "?"
            
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.info(f"Favorito de {cli}: **{fav}**")
                # Clique aqui atualiza apenas o fragmento CRM
                if st.button("🚀 ENVIAR PUSH"):
                    res = _safe_generate(f"Push curta e urgente para {cli} sobre {fav}. Emoji.")
                    st.session_state.update({'push_msg': res, 'push_item': fav})
            with c2:
                st.markdown(render_phone(st.session_state.get('push_item', 'Oferta'), st.session_state.get('push_msg', '...')), unsafe_allow_html=True)

# --- FRAGMENTO: CHAT (Já estava correto, mantido) ---
@st.fragment
def render_chat_tab():
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.markdown("""<div class="css-card"><h4 style='color:#EA1D2C; margin:0;'>Genius Assistant 💬</h4><p style='font-size:0.9rem; color:#555;'>Pergunte sobre seus dados de vendas.</p></div>""", unsafe_allow_html=True)

        if 'chat_history' not in st.session_state: st.session_state['chat_history'] = []

        def process_submit():
            val = st.session_state.get("chat_input_widget")
            if val:
                st.session_state['chat_history'].append({'role': 'user', 'text': val})
                resposta = "Analisando..."
                ctx = ""
                if os.path.exists('vendas_restaurante.csv') and model:
                    try:
                        df = pd.read_csv('vendas_restaurante.csv')
                        ctx = df.tail(30).to_string(index=False)
                        prompt = f"Dados: {ctx}. Pergunta: {val}. Responda curto e com emojis."
                        resposta = _safe_generate(prompt)
                    except: resposta = "Erro ao ler dados."
                else:
                    resposta = "Sistema Offline."
                st.session_state['chat_history'].append({'role': 'assistant', 'text': resposta})
                st.session_state.chat_input_widget = ""

        def click_suggestion(txt):
            st.session_state.chat_input_widget = txt
            st.session_state['chat_history'].append({'role': 'user', 'text': txt})
            ctx = ""
            if os.path.exists('vendas_restaurante.csv'): 
                ctx = pd.read_csv('vendas_restaurante.csv').tail(30).to_string(index=False)
            resp = _safe_generate(f"Dados: {ctx}. Pergunta: {txt}. Responda curto e com emojis.")
            st.session_state['chat_history'].append({'role': 'assistant', 'text': resp})
            st.session_state.chat_input_widget = ""

        st.text_input("Digite sua pergunta:", key="chat_input_widget", on_change=process_submit)
        st.button("Enviar Pergunta", on_click=process_submit)

        history = st.session_state['chat_history']
        pairs = []
        buffer = []
        for msg in history:
            buffer.append(msg)
            if len(buffer) == 2:
                pairs.append(buffer)
                buffer = []
        if buffer: pairs.append(buffer)
        
        st.write("") 
        for pair in reversed(pairs):
            user_msg = pair[0]
            st.markdown(f"""
            <div style="text-align:right; margin-bottom:5px;">
                <span style="background:#F3F4F6; color:#333; padding:10px 15px; border-radius:15px 15px 0 15px; display:inline-block; font-weight:600; font-size:0.9rem;">
                    {user_msg['text']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            if len(pair) > 1:
                ai_msg = pair[1]
                st.markdown(f"""
                <div style="text-align:left; margin-bottom:25px;">
                    <span style="background:#FFF0F0; color:#EA1D2C; border:1px solid #FECACA; padding:10px 15px; border-radius:15px 15px 15px 0; display:inline-block; font-size:0.9rem;">
                        🤖 <strong>Genius:</strong> {ai_msg['text']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    with c_right:
        st.info("💡 **Dicas:**")
        st.button("💰 Faturamento Total?", on_click=click_suggestion, args=("Qual o faturamento total?",))
        st.button("🏆 Melhor Cliente?", on_click=click_suggestion, args=("Quem é o melhor cliente?",))
        st.button("🍔 Item mais vendido?", on_click=click_suggestion, args=("Item mais vendido?",))

# ==============================================================================
# 4. CONTEÚDO PRINCIPAL (ORQUESTRAÇÃO)
# ==============================================================================
st.write("") 

# Cria as abas estáticas
tab_sup, tab_vend, tab_crm, tab_chat = st.tabs(["🛡️ Central de Suporte", "💰 Engenharia de Vendas", "🎯 CRM Preditivo", "🤖 Genius Assistant"])

# Renderiza cada aba dentro de seu contexto, chamando os fragmentos
with tab_sup:
    render_support_tab()

with tab_vend:
    render_sales_tab()

with tab_crm:
    render_crm_tab()

with tab_chat:
    render_chat_tab()