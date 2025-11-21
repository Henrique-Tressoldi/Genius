import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import Counter
import time
import os
import base64

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILOS (Separado para não quebrar)
# ==============================================================================
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Ifood_logo.svg/2560px-Ifood_logo.svg.png"

# Tenta carregar imagem local `ifood_Logo.png` e embuti-la como data URI (garante exibição)
LOCAL_HEADER_LOGO = "ifood_Logo.png"
if os.path.exists(LOCAL_HEADER_LOGO):
    try:
        with open(LOCAL_HEADER_LOGO, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            # assume PNG or try to detect from filename
            mime = "image/png"
            if LOCAL_HEADER_LOGO.lower().endswith(".jpg") or LOCAL_HEADER_LOGO.lower().endswith(".jpeg"):
                mime = "image/jpeg"
            LOGO_URL = f"data:{mime};base64,{encoded}"
    except Exception:
        pass

# Ícone local (prefere versão arredondada `ifoo_logo_round.png` se existir)
ICON_PATH = "ifood_icon.jpg"
ROUND_ICON = "ifood_icon_round.png"

# Tenta gerar ícone arredondado em tempo de execução se Pillow estiver disponível.
def _try_generate_round_icon(src, out):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    try:
        if not os.path.exists(out) and os.path.exists(src):
            img = Image.open(src).convert("RGBA")
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side)).resize((256, 256), Image.LANCZOS)
            mask = Image.new("L", (256, 256), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 256, 256), fill=255)
            img.putalpha(mask)
            img.save(out, format="PNG")
            return True
    except Exception:
        return False
    return False

# Tenta criar o ícone arredondado (não gera erro se falhar)
# Tenta gerar o ícone arredondado (se Pillow estiver disponível)
_try_generate_round_icon(ICON_PATH, ROUND_ICON)

# Use o ícone local preferencialmente: versão arredondada se existir, senão
# a imagem original `ifood_icon.jpg`. Só em último caso use `LOGO_URL`.
if os.path.exists(ROUND_ICON):
    page_icon = ROUND_ICON
elif os.path.exists(ICON_PATH):
    page_icon = ICON_PATH
else:
    page_icon = LOGO_URL if LOGO_URL else "🔴"

st.set_page_config(
    page_title="iFood Partner Portal",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função de rerun compatível com várias versões do Streamlit
def _safe_rerun():
    try:
        # Método público (padrão)
        st.experimental_rerun()
        return
    except Exception:
        pass
    # Tentativas com exceções internas de diferentes versões
    try:
        from streamlit.runtime.scriptrunner.script_runner import RerunException
        raise RerunException()
    except Exception:
        pass
    try:
        from streamlit.web.server.server import RerunException
        raise RerunException()
    except Exception:
        pass
    try:
        # Último recurso: reinicia o processo (força reload)
        import sys
        sys.exit(0)
    except Exception:
        return

def carregar_css():
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
        * {{ font-family: 'Nunito Sans', sans-serif !important; }}
        
        /* Layout Geral */
        [data-testid="stAppViewContainer"] {{ background-color: #F7F7F7 !important; }}
        .main .block-container {{ padding-top: 120px !important; padding-left: 3rem !important; padding-right: 3rem !important; max-width: 100%; }}
        
        /* Texto Geral */
        /*p, h1, h2, h3, h4, div, label, li {{ color: #1F2937 !important; }}*/

        /* --- CORREÇÃO DROPDOWN (Menu Preto no Branco) --- */
        div[data-baseweb="select"] > div {{ background-color: #FFFFFF !important; color: #000000 !important; }}
        div[data-baseweb="select"] span {{ color: #000000 !important; }}
        ul[data-baseweb="menu"] {{ background-color: #FFFFFF !important; }}
        li[data-baseweb="option"] {{ color: #000000 !important; }}
        li[data-baseweb="option"]:hover {{ background-color: #FEE2E2 !important; color: #EA1D2C !important; font-weight: bold !important; }}
        /* --- SELECTBOX / LISTAS: garantir fundo branco e texto legível --- */
        /* Regras amplas para cobrir overlays e portais do BaseWeb/React */
        div[data-testid="stSelectbox"], div[data-testid="stSelectbox"] div, div[role="listbox"], div[role="option"], select, option,
        body div[role="listbox"], body ul[data-baseweb="menu"], body li[data-baseweb="option"],
        .rc-virtual-list, .rc-virtual-list-holder, .baseweb-select-menu, .baseweb-select-option {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }}
        div[role="option"]:hover, li[data-baseweb="option"]:hover, .baseweb-select-option:hover {{ background-color: #F3F4F6 !important; color: #000000 !important; }}
        /* Força contraste do item selecionado dentro do input do select */
        div[data-testid="stSelectbox"] > div, div[data-baseweb="select"] > div {{ background-color: #FFFFFF !important; color: #000000 !important; }}
        
        /* Sidebar: do not force a red background on Streamlit sidebar in deployed app */
        /* Keep default Streamlit sidebar styling to avoid breaking the hosted layout. */

        /* --- COMPONENTES VISUAIS --- */
        .css-card {{ background-color: #FFFFFF !important; border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #EEE; margin-bottom: 20px; }}
        .metric-box {{ background: #FFF; padding: 20px; border-radius: 12px; border: 1px solid #E0E0E0; text-align: center; }}
        .ai-result-box {{ background-color: #F0FDF4 !important; border: 1px solid #BBF7D0 !important; border-radius: 12px; padding: 20px; margin-top: 15px; color: #14532D !important; }}
        .ai-result-box strong {{ color: #14532D !important; }}
        
        /* Botões e Tags */
        .stButton button {{ background-color: #EA1D2C !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; }}
        .stButton button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(234, 29, 44, 0.3); }}
        .status-tag {{ padding: 6px 14px; border-radius: 100px; font-size: 12px; font-weight: 800; text-transform: uppercase; }}
        .tag-URGENTE {{ background: #FEE2E2; color: #DC2626 !important; }}
        .tag-MEDIA {{ background: #FEF3C7; color: #D97706 !important; }}
        .tag-BAIXA {{ background: #D1FAE5; color: #059669 !important; }}

        /* Esconde elementos padrão */
        header[data-testid="stHeader"] {{ display: none; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        /* Style específico para inputs do app (inclui o campo do chat) */
        /* Alvo amplo: inputs de texto gerados pelo Streamlit e textareas */
        .stTextInput > div > div > input,
        input[type="text"],
        textarea,
        input[aria-label="Pergunte ao Genius Assistant"],
        input[aria-label="Digite sua pergunta:"]
        {{
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #E6E6E6 !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
            padding: 12px 14px !important;
            border-radius: 12px !important;
        }}
        .stTextInput > div > div > input::placeholder,
        input::placeholder,
        textarea::placeholder {{ color: #9CA3AF !important; }}
        /* Header custom (usar classe para facilitar overrides responsivos) */
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
            padding: 0 30px 0 370px;
            z-index: 9999;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        }}

        /* Ajustes responsivos */
        @media (max-width: 1000px) {{
            .top-app-header {{ padding: 0 20px !important; height: 72px !important; }}
            .main .block-container {{ padding-top: 110px !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }}
            /* keep default sidebar width on small screens */
        }}

        @media (max-width: 700px) {{
            .top-app-header {{
                flex-direction: column !important;
                align-items: flex-start !important;
                gap: 8px !important;
                padding: 12px !important;
                height: auto !important;
            }}
            .top-app-header .header-left {{ display:flex; align-items:center; gap:10px; }}
            .top-app-header .header-right {{ display:flex; align-items:center; gap:12px; width:100%; justify-content:space-between; }}
            .main .block-container {{ padding-top: 160px !important; padding-left: 12px !important; padding-right: 12px !important; }}
            /* leave sidebar positioning to Streamlit default on very small screens */
            .css-card {{ padding: 16px !important; }}
            .metric-box {{ padding: 14px !important; }}
        }}
    </style>

    <div class="top-app-header">
        <div class="header-left" style="display:flex; align-items:center; gap:15px;">
                <img src="{LOGO_URL}" style="width:108px; height:108px; border-radius:14px; object-fit:cover;" alt="iFood logo"/>
                <span style="color:#ccc; font-size:1.2rem;">|</span>
                <span style="font-size:1.1rem; font-weight:600; color:#555;">Portal do Parceiro</span>
            </div>
        <div class="header-right" style="display:flex; align-items:center; gap:20px;">
            <div style="text-align:right; line-height:1.2;">
                <div style="font-size:15px; font-weight:700; color:#333;">Minha Loja</div>
                <div style="font-size:12px; color:#00A85A; font-weight:700;">● LOJA ABERTA</div>
            </div>
            <div style="width:45px; height:45px; background:#EA1D2C; border-radius:50%; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.2rem;">L</div>
        </div>
    </div>
    """

st.markdown(carregar_css(), unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES AUXILIARES (HTML DO CELULAR SEPARADO)
# ==============================================================================
def render_phone_mockup(item, msg):
    return f"""
    <div style="border: 14px solid #222; border-radius: 36px; background: #fff; max-width: 300px; margin:0 auto; box-shadow: 0 30px 60px rgba(0,0,0,0.3); overflow:hidden;">
        <div style="background:#F5F5F5; height:30px; text-align:center; font-size:10px; padding-top:8px; font-weight:bold; color:#333;">12:42</div>
        <div style="padding:20px; height:450px; background: linear-gradient(135deg, #EA1D2C 0%, #C20E1B 100%);">
            <div style="background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-top: 30px; border-left: 5px solid #EA1D2C; font-family: sans-serif;">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="font-size:10px; font-weight:bold; color:#333 !important;">IFOOD • AGORA</span>
                    <span style="font-size:10px; color:#666 !important;">1m</span>
                </div>
                <div style="font-size:12px; font-weight:800; color:#000 !important; margin-bottom:3px;">{item} PRA VOCÊ! 😋</div>
                <div style="font-size:11px; color:#444 !important; line-height:1.3;">{msg}</div>
            </div>
        </div>
    </div>
    """

# ==============================================================================
# 3. BACKEND (IA E LÓGICA)
# ==============================================================================
# Tenta pegar dos segredos do Streamlit, ou usa vazio se não achar
try:
    DEFAULT_KEY = st.secrets["GEMINI_KEY"]
except:
    DEFAULT_KEY = ""

@st.cache_resource
def get_model(api_key):
    if not api_key: return None, None
    try:
        genai.configure(api_key=api_key)
        safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        for m in genai.list_models():
            if 'flash' in m.name.lower() and 'exp' not in m.name.lower():
                return genai.GenerativeModel(m.name), safety
        return genai.GenerativeModel('gemini-1.5-pro'), safety
    except: return None, None

# ==============================================================================
# Sidebar removed: user requested no sidebar UI. Initialize model programmatically
# ==============================================================================
# Initialize model using DEFAULT_KEY (no sidebar input). If you want to provide
# an API key dynamically, set DEFAULT_KEY or update this code to read from env.
model, safety = get_model(DEFAULT_KEY)

# ==============================================================================
# 5. CONTEÚDO PRINCIPAL
# ==============================================================================
st.write("") # Espaço para o header fixo

tab_sup, tab_vend, tab_crm, tab_chat = st.tabs(["🛡️ Central de Suporte", "💰 Engenharia de Vendas", "🎯 CRM Preditivo", "🤖 Genius Assistant"])

# --- ABA SUPORTE ---
with tab_sup:
    if os.path.exists('suporte_ifood_simulado.csv'):
        df = pd.read_csv('suporte_ifood_simulado.csv')
        count = len(df)
    else: count = 0
    
    st.write("")
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.markdown(f"""<div class="css-card" style="border-left:8px solid #EA1D2C;">
            <h5 style="color:#666; margin:0;">FILA DE ATENDIMENTO</h5>
            <h1 style="margin:10px 0; font-size:4rem; color:#333;">{count}</h1>
            <strong style="color:#EA1D2C;">Tickets Pendentes</strong></div>""", unsafe_allow_html=True)
        if st.button("⚡ INICIAR TRIAGEM AUTOMÁTICA"):
            st.session_state['processed'] = True

    with col_r:
        if st.session_state.get('processed') and count > 0:
            st.markdown("##### 📋 Análise em Tempo Real")
            for i, row in df.head(3).iterrows():
                msg = row['mensagem_cliente']
                prompt = f"Classifique (URGENTE/MEDIA/BAIXA) e justifique em 1 frase: '{msg}'"
                res = model.generate_content(prompt, safety_settings=safety).text.strip() if model else "Offline"
                
                tag, cls = ("BAIXA", "tag-BAIXA")
                if "URGENTE" in res.upper(): tag, cls = "URGENTE", "tag-URGENTE"
                elif "MEDIA" in res.upper(): tag, cls = "MÉDIA", "tag-MEDIA"
                
                st.markdown(f"""<div class="css-card" style="padding:20px; margin-bottom:15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#EA1D2C; font-weight:800;">CHAMADO #{i+1}</span>
                        <span class="status-tag {cls}">{tag}</span>
                    </div>
                    <div style="margin:12px 0; font-weight:600; font-size:1.1rem; color:#333;">"{msg}"</div>
                    <div style="background:#F5F5F5; padding:10px; border-radius:8px; font-size:0.9rem; color:#555;">
                        🤖 <strong>Genius:</strong> {res}
                    </div>
                </div>""", unsafe_allow_html=True)
                time.sleep(0.1)

# --- ABA VENDAS ---
with tab_vend:
    st.write("")
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        itens = []
        for i in df_v['itens']: itens.extend([x.strip() for x in str(i).split('+')])
        campeao = Counter(itens).most_common(1)[0][0]
        total_vendas = df_v['valor_total'].sum()
        
        # CARTÕES DE MÉTRICA HTML
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div class="metric-box"><div style="color:#888; font-weight:700; font-size:0.8rem; letter-spacing:1px;">FATURAMENTO</div><div style="color:#333; font-weight:800; font-size:2.2rem; margin:5px 0;">R$ {total_vendas:.2f}</div><div style="color:#00A85A; font-weight:bold; font-size:0.8rem;">▲ +12% vs Ontem</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-box"><div style="color:#888; font-weight:700; font-size:0.8rem; letter-spacing:1px;">TOTAL PEDIDOS</div><div style="color:#333; font-weight:800; font-size:2.2rem; margin:5px 0;">{len(df_v)}</div><div style="color:#666; font-size:0.8rem;">Hoje</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-box"><div style="color:#888; font-weight:700; font-size:0.8rem; letter-spacing:1px;">ITEM CAMPEÃO</div><div style="color:#EA1D2C; font-weight:800; font-size:1.8rem; margin:5px 0;">{campeao.upper()}</div><div style="color:#666; font-size:0.8rem;">Maior Conversão</div></div>""", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        c_ia, c_table = st.columns([1, 2])
        with c_ia:
            st.markdown(f"""<div class="css-card"><h3 style="color:#EA1D2C; margin-top:0;">Insight Genius 💡</h3><p style="font-size:1rem; line-height:1.5; color:#444;">O item <strong>{campeao}</strong> é responsável por grande parte das vendas. <br><br>A IA sugere criar um combo estratégico.</p></div>""", unsafe_allow_html=True)
            if st.button("✨ GERAR OFERTA AGORA"):
                with st.spinner("Analisando..."):
                    prompt = f"Crie nome de combo e descrição curta para {campeao} + Batata. Sem titulos. Formato texto simples."
                    res = model.generate_content(prompt, safety_settings=safety).text if model else "Erro IA"
                    if res:
                        # CORREÇÃO: MOSTRAR RESULTADO EM CAIXA VISÍVEL
                        st.markdown(f"""<div class="ai-result-box"><strong>✅ Sugestão Gerada:</strong><br><br>{res.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)
                    else: st.error("Tente novamente.")
        
        with c_table:
            st.markdown("##### 📋 Últimos Pedidos")
            st.dataframe(df_v, use_container_width=True, height=500)

# --- ABA CRM ---
with tab_crm:
    st.write("")
    if os.path.exists('vendas_restaurante.csv'):
        df_v = pd.read_csv('vendas_restaurante.csv')
        if 'cliente' in df_v.columns:
            cli = df_v['cliente'].unique()
            
            c_l, c_r = st.columns([1.5, 1])
            with c_l:
                st.markdown("### Segmentação Inteligente")
                # O CSS lá em cima já corrigiu as cores deste Selectbox
                target = st.selectbox("Selecione o Cliente:", cli)
                
                hist = df_v[df_v['cliente'] == target]
                itens_c = []
                for i in hist['itens']: itens_c.extend([x.strip() for x in str(i).split('+')])
                
                if itens_c:
                    fav = Counter(itens_c).most_common(1)[0][0]
                    st.markdown(f"""<div class="css-card"><div style="display:flex; justify-content:space-between; align-items:center;"><div><small style="color:#999; font-weight:bold;">CLIENTE</small><br><span style="font-size:1.4rem; font-weight:700;">{target}</span></div><div style="text-align:right;"><small style="color:#999; font-weight:bold;">PRATO PREFERIDO</small><br><span style="font-size:1.4rem; font-weight:700; color:#EA1D2C;">{fav.upper()}</span></div></div></div>""", unsafe_allow_html=True)
                    
                    if st.button("🚀 ENVIAR PUSH NOTIFICATION"):
                        prompt = f"Aja como iFood. Cliente: {target}. Favorito: {fav}. Escreva 1 push curta, urgente, emoji. Sem listas. Texto puro."
                        res = model.generate_content(prompt, safety_settings=safety).text.strip() if model else "Offline"
                        st.session_state['push_msg'] = res
                        st.session_state['push_item'] = fav
            
            with c_r:
                msg = st.session_state.get('push_msg', "Aguardando...")
                item = st.session_state.get('push_item', "OFERTA").upper()
                # Chama a função que gera o HTML do celular
                st.markdown(render_phone_mockup(item, msg), unsafe_allow_html=True)
        else:
            st.error("Coluna 'cliente' não encontrada no CSV.")

# --- ABA GENIUS ASSISTANT ---
with tab_chat:
    st.write("")
    # Layout: 2/3 para Chat, 1/3 para Sugestões
    c_left, c_right = st.columns([2, 1])

    # Função interna para processar a pergunta sem duplicar
    def processar_pergunta(texto_pergunta):
        if not texto_pergunta: return
        
        # 1. Evita duplicidade: Se a última mensagem for igual, ignora
        hist = st.session_state.get('chat_history', [])
        if len(hist) > 0 and hist[-1]['role'] == 'user' and hist[-1]['text'] == texto_pergunta:
            return

        # 2. Adiciona pergunta ao histórico
        st.session_state['chat_history'].append({'role': 'user', 'text': texto_pergunta})
        
        # 3. Gera resposta da IA
        resposta = "Offline"
        if os.path.exists('vendas_restaurante.csv') and model:
            try:
                df = pd.read_csv('vendas_restaurante.csv')
                # Usa apenas as últimas 50 linhas para economizar tokens e ser rápido
                ctx = df.tail(50).to_string(index=False)
                
                prompt = f"""
                Atue como um Analista de BI do iFood.
                Analise os dados recentes de vendas abaixo:
                {ctx}
                
                PERGUNTA DO USUÁRIO: {texto_pergunta}
                
                Responda de forma curta, direta (máx 2 frases) e use emojis.
                """
                
                # Chama a IA
                resposta = model.generate_content(prompt, safety_settings=safety).text.strip()
            except: 
                resposta = "Erro ao processar IA."
        
        # 4. Adiciona resposta ao histórico
        st.session_state['chat_history'].append({'role': 'assistant', 'text': resposta})

    with c_left:
        st.markdown("""<div class="css-card"><h4 style='color:#EA1D2C; margin:0;'>Genius Assistant 💬</h4><p style='font-size:0.9rem; color:#555;'>Pergunte sobre seus dados de vendas.</p></div>""", unsafe_allow_html=True)

        # Inicializa histórico
        if 'chat_history' not in st.session_state: 
            st.session_state['chat_history'] = []

        # --- 1. ÁREA DE INPUT (FIXA NO TOPO) ---
        with st.form(key='chat_form', clear_on_submit=True):
            u_input = st.text_input("Digite sua pergunta:", placeholder="Ex: Qual cliente comprou mais?", key="top_chat_input")
            
            # Botão de envio dentro do form
            if st.form_submit_button("Enviar Pergunta"):
                processar_pergunta(u_input)
                _safe_rerun() # Reinicia para mostrar a resposta imediatamente

        # --- 2. ÁREA DE MENSAGENS (ORDEM INVERSA) ---
        # Vamos criar pares [Pergunta, Resposta] e mostrar os mais novos primeiro
        history = st.session_state['chat_history']
        
        # Agrupa em pares para exibição correta
        pairs = []
        buffer = []
        for msg in history:
            buffer.append(msg)
            if len(buffer) == 2: # Temos uma pergunta e uma resposta
                pairs.append(buffer)
                buffer = []
        
        # Se sobrou uma pergunta sem resposta (processando), adiciona também
        if buffer: pairs.append(buffer)
        
        # Exibe de trás para frente (Newest First)
        st.write("") # Espaço
        for pair in reversed(pairs):
            # Mensagem do Usuário
            user_msg = pair[0]
            st.markdown(f"""
            <div style="text-align:right; margin-bottom:5px;">
                <span style="background:#F3F4F6; color:#333; padding:10px 15px; border-radius:15px 15px 0 15px; display:inline-block; font-weight:600; font-size:0.9rem;">
                    {user_msg['text']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Resposta da IA (se houver)
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
        st.info("💡 **Sugestões Rápidas:**")
        
        # Botões que acionam a pergunta automaticamente
        if st.button("💰 Faturamento Total?"):
            processar_pergunta("Qual o faturamento total somando tudo?")
            _safe_rerun()
            
        if st.button("🏆 Melhor Cliente?"):
            processar_pergunta("Quem é o cliente que mais gastou?")
            _safe_rerun()
            
        if st.button("🍔 Item mais vendido?"):
            processar_pergunta("Qual o produto mais vendido?")
            _safe_rerun()