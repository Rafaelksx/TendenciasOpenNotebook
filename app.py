import streamlit as st
import requests
import os
from src.config import CUSTOM_CSS, SVG_LOGO, LLM_MODEL, EMBEDDING_MODEL

# Si la variable de entorno API_HOST existe, la usa. Si no, usa localhost.
api_host = os.getenv("API_HOST", "localhost")
url = f"http://{api_host}:8000/login"
# Variables globales de sesión necesarias antes de cargar vistas
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None


# Variables globales de sesión necesarias antes de cargar vistas
if "current_session_id" not in st.session_state:
    import time
    st.session_state.current_session_id = f"session_{int(time.time())}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ESTAS SON LAS DOS LÍNEAS NUEVAS ---
if "llm_model" not in st.session_state:
    st.session_state.llm_model = LLM_MODEL

if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = EMBEDDING_MODEL
# ---------------------------------------

# --- CONFIGURACIÓN BASE ---
st.set_page_config(
    page_title="Open Notebook - RAG Local", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar los estilos que ya tenías
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================================
# 🛑 1. EL PORTERO: LOGIN Y REGISTRO (Separados)
# ==========================================================
if 'modo_registro' not in st.session_state:
    st.session_state.modo_registro = False

if st.session_state['usuario'] is None:
    st.markdown("<h1 style='text-align: center;'>📖 Open Notebook</h1>", unsafe_allow_html=True)
    
    if not st.session_state.modo_registro:
        # --- FORMULARIO DE LOGIN ---
        st.markdown("<h3 style='text-align: center; color: #94a3b8;'>Inicia sesión</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            correo = st.text_input("Correo Electrónico")
            clave = st.text_input("Contraseña", type="password")
            
            col1, col2 = st.columns([1, 1])
            entrar = col1.form_submit_button("Entrar", use_container_width=True)
            ir_registro = col2.form_submit_button("¿No tienes cuenta? Regístrate")
            
            if entrar:
                respuesta = requests.post(url, json={"correo": correo, "contraseña": clave})
                if respuesta.status_code == 200:
                    st.session_state['usuario'] = respuesta.json()['usuario']
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
            
            if ir_registro:
                st.session_state.modo_registro = True
                st.rerun()
                
    else:
        # --- FORMULARIO DE REGISTRO ---
        st.markdown("<h3 style='text-align: center; color: #94a3b8;'>Crear cuenta nueva</h3>", unsafe_allow_html=True)
        with st.form("register_form"):
            nombre = st.text_input("Nombre completo")
            correo = st.text_input("Correo electrónico")
            clave = st.text_input("Contraseña", type="password")
            
            col1, col2 = st.columns([1, 1])
            registrar = col1.form_submit_button("Registrarme", use_container_width=True)
            volver = col2.form_submit_button("Volver al Login")
            
            if registrar:
                respuesta = requests.post("http://localhost:8000/registro", json={"nombre": nombre, "correo": correo, "contraseña": clave})
                if respuesta.status_code == 200:
                    st.success("¡Registro exitoso! Ya puedes entrar.")
                    st.session_state.modo_registro = False
                    st.rerun()
                else:
                    st.error("Error al registrar: el correo podría estar en uso.")
            
            if volver:
                st.session_state.modo_registro = False
                st.rerun()
    st.stop()
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

# El sidebar ahora incluye el botón de logout internamente
sidebar.render()

tab_chat, tab_explorer, tab_upload = st.tabs(["Chat de Consulta", "Explorador de Documentos", "Cargar Archivos"])

with tab_chat: chat.render()
with tab_explorer: explorer.render()
with tab_upload: upload.render()