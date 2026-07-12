import streamlit as st
import requests
import os
from src.config import CUSTOM_CSS, SVG_LOGO, LLM_MODEL, EMBEDDING_MODEL

# --- CONFIGURACIÓN BASE ---
st.set_page_config(
    page_title="Open Notebook - RAG Local", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
PASTEL_GLASS_CSS = '''
<style>
/* Fondo Mesh Gradient  */
.stApp {
    background: radial-gradient(circle at 10% 90%, #ffdfd3 0%, transparent 50%),
                radial-gradient(circle at 90% 10%, #a1c4fd 0%, transparent 50%),
                linear-gradient(135deg, #fdfbfb 0%, #f3f4f6 100%);
    background-attachment: fixed;
}

/* Forzar todo el texto a colores oscuros (Incluye listas y negritas) */
.stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span, label, .stTab, .stMarkdown li, .stMarkdown ul, .stMarkdown ol, .stMarkdown strong, .stMarkdown em, .stMarkdown a {
    color: #0f172a !important;
}

/* Contenedor del Login */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 24px !important;
    padding: 3rem !important;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1) !important;
    max-width: 420px !important;
    margin: 40px auto !important;
}

/* Inputs de texto estilo*/
div[data-testid="stTextInput"] > div > div > input {
    background: rgba(255, 255, 255, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    color: #0f172a !important;
    border-radius: 12px !important;
    padding: 12px !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    backdrop-filter: blur(5px) !important;
}

div[data-testid="stTextInput"] > div > div > input:focus {
    background: rgba(255, 255, 255, 0.9) !important;
    border-color: #a1c4fd !important;
    box-shadow: 0 0 0 3px rgba(161, 196, 253, 0.4) !important;
}

/* Etiquetas de los inputs */
.stTextInput label {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px !important;
}

/* BOTONES GLOBALES */
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: rgba(255, 255, 255, 0.35) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.9) !important;
    border-radius: 16px !important;
    color: #1e293b !important;
    font-weight: 700 !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
    width: 100% !important;
}

.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(255, 255, 255, 0.7) !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
    border-color: #ffffff !important;
}

/* Titulos especificos del login */
h1.glass-title {
    text-align: center;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 2.8rem;
    margin-bottom: 5px;
    letter-spacing: -1px;
}

h3.glass-subtitle {
    text-align: center;
    color: #475569 !important;
    font-weight: 500;
    font-size: 1.1rem;
    margin-bottom: 30px;
}
</style>
'''
st.markdown(PASTEL_GLASS_CSS, unsafe_allow_html=True)


# Si la variable de entorno API_HOST existe, la usa. Si no, usa localhost.
api_host = os.getenv("API_HOST", "localhost")
url = f"http://{api_host}:8000/login"

# Variables globales de sesión necesarias antes de cargar vistas
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None

# Auto-login con query_params
if st.session_state['usuario'] is None:
    uid_param = st.query_params.get('uid')
    if uid_param:
        try:
            resp = requests.get(f"http://{api_host}:8000/usuario/{uid_param}", timeout=3)
            if resp.status_code == 200:
                st.session_state['usuario'] = resp.json()
            else:
                st.query_params.clear()
        except Exception:
            pass


# Variables globales de sesión necesarias antes de cargar vistas
if "current_session_id" not in st.session_state:
    import time
    st.session_state.current_session_id = f"session_{int(time.time())}"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "llm_model" not in st.session_state:
    st.session_state.llm_model = LLM_MODEL

if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = EMBEDDING_MODEL
# ---------------------------------------

# Aplicar los estilos que ya tenías
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================================
# 🛑 1. EL PORTERO: LOGIN Y REGISTRO (Separados)
# ==========================================================
if 'modo_registro' not in st.session_state:
    st.session_state.modo_registro = False

if st.session_state['usuario'] is None:
    # Titulos con clases CSS actualizadas
    st.markdown("<h1 class='glass-title'>Open Notebook</h1>", unsafe_allow_html=True)
    
    if not st.session_state.modo_registro:
        if st.session_state.get('registro_exitoso'):
            st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
            st.toast("¡Registro exitoso!", icon="🎉")
            del st.session_state['registro_exitoso']
            
        # --- FORMULARIO DE LOGIN ---
        st.markdown("<h3 class='glass-subtitle'>Inicia sesión en tu entorno RAG</h3>", unsafe_allow_html=True)
        col_space1, col_form, col_space2 = st.columns([1, 1.5, 1])
        
        with col_form:
            with st.form("login_form"):
                correo = st.text_input("Correo Electrónico", placeholder="tu@email.com")
                clave = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
                entrar = st.form_submit_button("Entrar", use_container_width=True)
                ir_registro = st.form_submit_button("Crear una cuenta nueva", use_container_width=True)
                
                if entrar:
                    try:
                        resp = requests.post(
                            f"http://{api_host}:8000/login",
                            json={"correo": correo, "contraseña": clave},
                            timeout=5
                        )
                        if resp.status_code == 200:
                            usuario_data = resp.json()["usuario"]
                            st.session_state['usuario'] = usuario_data
                            st.query_params['uid'] = str(usuario_data['id'])
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Credenciales incorrectas."))
                    except Exception as e:
                        st.error(f"No se pudo conectar con el backend: {e}")
                
                if ir_registro:
                    st.session_state.modo_registro = True
                    st.rerun()
                
    else:
        # --- FORMULARIO DE REGISTRO ---
        st.markdown("<h3 class='glass-subtitle'>Regístrate para comenzar a indexar</h3>", unsafe_allow_html=True)
        col_space1, col_form, col_space2 = st.columns([1, 1.5, 1])
        
        with col_form:
            with st.form("register_form"):
                nombre = st.text_input("Nombre completo", placeholder="Ej: Fernando Centeno")
                correo = st.text_input("Correo electrónico", placeholder="tu@email.com")
                clave = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
                registrar = st.form_submit_button("Registrarme", use_container_width=True)
                volver = st.form_submit_button("Volver al Login", use_container_width=True)
                
                if registrar:
                    if not nombre or not correo or not clave:
                        st.error("Por favor, completa todos los campos.")
                    else:
                        try:
                            resp = requests.post(
                                f"http://{api_host}:8000/registro",
                                json={"nombre": nombre, "correo": correo, "contraseña": clave},
                                timeout=5
                            )
                            if resp.status_code == 200:
                                st.session_state['registro_exitoso'] = True
                                st.session_state.modo_registro = False
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Error al registrar."))
                        except Exception as e:
                            st.error(f"No se pudo conectar con el backend: {e}")
                
                if volver:
                    st.session_state.modo_registro = False
                    st.rerun()
    st.stop()
if st.session_state['usuario'] is not None:
    # ==========================================================
    # 🟢 2. LA APLICACIÓN
    # ==========================================================
    st.markdown(f"""
<div class="brand-container">
{SVG_LOGO}
<h1 class="gradient-text">Open Notebook</h1>
</div>
""", unsafe_allow_html=True)

    st.markdown(f'<div class="gradient-subtitle">Usuario: {st.session_state["usuario"]["nombre"]} • Libreta inteligente local RAG</div>', unsafe_allow_html=True)

    from views import sidebar, chat, explorer, upload

    sidebar.render()

    if st.session_state['usuario'] is not None:
        tab_chat, tab_explorer, tab_upload = st.tabs(["Chat de Consulta", "Explorador de Documentos", "Cargar Archivos"])

        with tab_chat: chat.render()
        with tab_explorer: explorer.render()
        with tab_upload: upload.render()