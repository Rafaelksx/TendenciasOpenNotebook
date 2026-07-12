import streamlit as st
import requests
import time
from src.config import OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL
from src.db import get_vector_collection, get_chroma_client
from src.models import test_ollama_connection, get_installed_models
from src.history import get_chat_sessions, load_chat_session, delete_chat_session

# --- CSS ESPECÍFICO PARA EL SIDEBAR (Glassmorfismo Minimalista) ---
SIDEBAR_GLASS_CSS = '''
<style>
/* Forzar transparencia total en el contenedor base de Streamlit */
section[data-testid="stSidebar"] {
    background-color: transparent !important;
}

/* Aplicar el Glassmorfismo REAL a la capa contenedora interna */
section[data-testid="stSidebar"] > div {
    background: rgba(255, 255, 255, 0.15) !important; 
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.4) !important;
}

/* Forzar colores oscuros para toda la tipografía del panel */
section[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

/* Estilización de los menús desplegables (Selectbox) e inputs */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] input {
    background: rgba(255, 255, 255, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px !important;
    color: #0f172a !important;
    font-weight: 500 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
}

/* Título Principal */
.sidebar-title {
    color: #0f172a !important;
    font-weight: 800;
    font-size: 1.4rem;
    margin-bottom: 0;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.5px;
}

/* Subtítulos de cada sección */
.sidebar-subtitle {
    font-size: 0.75rem;
    font-weight: 800;
    color: #0047ff !important; 
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 20px;
    margin-bottom: 10px;
}

/* Cápsula de Estado */
.status-capsule {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.4) !important;
    backdrop-filter: blur(10px) !important;
    padding: 8px 14px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    font-weight: 700;
    font-size: 0.85rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

.neon-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 10px;
}
.dot-on { background: #10b981; }
.dot-off { background: #ef4444; }

/* Ajustes para las métricas */
[data-testid="stMetricValue"] {
    font-weight: 800 !important;
    color: #0047ff !important;
}
[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    color: #475569 !important;
}
</style>
'''

def render():
    st.markdown(SIDEBAR_GLASS_CSS, unsafe_allow_html=True)

    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)

    st.sidebar.markdown("<h2 class='sidebar-title'>Panel de Control</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state['usuario'] = None
        st.session_state.messages = []
        st.query_params.clear()
        st.rerun()

    st.sidebar.markdown("---")

    ollama_connected = test_ollama_connection()
    installed_models = get_installed_models() if ollama_connected else []

    if ollama_connected:
        st.sidebar.markdown('''
            <div class="status-capsule">
                <div class="neon-dot dot-on"></div>
                Ollama Conectado
            </div>
        ''', unsafe_allow_html=True)
        st.sidebar.markdown(f"**Dirección:** `{OLLAMA_BASE_URL}`")
        
        st.sidebar.markdown("<p class='sidebar-subtitle'>Modelos</p>", unsafe_allow_html=True)
        
        llm_options = installed_models if installed_models else [LLM_MODEL]
        default_llm_idx = llm_options.index(st.session_state.llm_model) if st.session_state.llm_model in llm_options else (llm_options.index(LLM_MODEL) if LLM_MODEL in llm_options else 0)
            
        st.session_state.llm_model = st.sidebar.selectbox("Modelo de Lenguaje (LLM):", options=llm_options, index=default_llm_idx)
        
        emb_options = installed_models if installed_models else [EMBEDDING_MODEL]
        default_emb_idx = emb_options.index(st.session_state.embedding_model) if st.session_state.embedding_model in emb_options else (emb_options.index(EMBEDDING_MODEL) if EMBEDDING_MODEL in emb_options else 0)
            
        st.session_state.embedding_model = st.sidebar.selectbox("Modelo de Embeddings:", options=emb_options, index=default_emb_idx)
        
        st.sidebar.markdown("<p class='sidebar-subtitle'>Descargar</p>", unsafe_allow_html=True)
        model_to_pull = st.sidebar.text_input("Nombre del modelo:", key="pull_model_input_sidebar")
        
        if st.sidebar.button("Descargar Modelo", use_container_width=True):
            if model_to_pull:
                with st.sidebar.spinner(f"Descargando..."):
                    try:
                        pull_url = f"{OLLAMA_BASE_URL}/api/pull"
                        response = requests.post(pull_url, json={"name": model_to_pull.strip(), "stream": False}, timeout=600)
                        if response.status_code == 200:
                            st.sidebar.success(f"¡{model_to_pull} descargado!")
                            st.rerun()
                        else:
                            st.sidebar.error("Error al descargar")
                    except Exception as e:
                        st.sidebar.error("Error de conexión")
            else:
                st.sidebar.warning("Introduce un nombre de modelo.")
    else:
        st.sidebar.markdown('''
            <div class="status-capsule">
                <div class="neon-dot dot-off"></div>
                Ollama Desconectado
            </div>
        ''', unsafe_allow_html=True)
        if st.sidebar.button("Reintentar Conexión"):
            st.rerun()

    # --- AJUSTES RAG ---
    st.sidebar.markdown("<p class='sidebar-subtitle'>Configuración RAG</p>", unsafe_allow_html=True)
    st.session_state.rag_k = st.sidebar.slider("Fragmentos (k):", min_value=1, max_value=10, value=4, step=1)
    st.session_state.similarity_threshold = st.sidebar.slider("Umbral:", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    # --- HISTORIAL ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p class='sidebar-subtitle'>Historial</p>", unsafe_allow_html=True)

    if st.sidebar.button("Nueva Conversación", use_container_width=True):
        new_sess = f"session_{int(time.time())}"
        st.session_state.current_session_id = new_sess
        st.session_state.messages = []
        st.session_state.session_select_box = new_sess
        st.rerun()

    sessions = get_chat_sessions(usuario_id)
    if sessions:
        session_options = {s[0]: s[1] for s in sessions}
        if st.session_state.current_session_id not in session_options:
            session_options[st.session_state.current_session_id] = "Conversación actual"
            
        selected_sess = st.sidebar.selectbox(
            "Seleccionar chat:", 
            options=list(session_options.keys()), 
            format_func=lambda x: session_options[x], 
            index=list(session_options.keys()).index(st.session_state.current_session_id) if st.session_state.current_session_id in session_options else 0,
            key="session_select_box"
        )
        
        if selected_sess != st.session_state.current_session_id:
            st.session_state.current_session_id = selected_sess
            st.session_state.messages = load_chat_session(usuario_id, selected_sess)
            st.rerun()
            
        if st.sidebar.button("Eliminar Chat", use_container_width=True):
            chroma_client = get_chroma_client()
            try: chroma_client.delete_collection(name=collection_name)
            except Exception: pass
            delete_chat_session(usuario_id, st.session_state.current_session_id)
            new_sess = f"session_{int(time.time())}"
            st.session_state.current_session_id = new_sess
            st.session_state.session_select_box = new_sess
            st.session_state.messages = []
            st.rerun()

    st.sidebar.markdown("---")
    all_metadata = collection.get()
    ingested_docs = list(set([m["source"] for m in all_metadata["metadatas"]])) if all_metadata and all_metadata["metadatas"] else []
    st.sidebar.markdown("<p class='sidebar-subtitle'>Estadísticas RAG</p>", unsafe_allow_html=True)
    st.sidebar.metric(label="Documentos", value=len(ingested_docs))
    st.sidebar.metric(label="Chunks", value=len(all_metadata["ids"]) if all_metadata and all_metadata["ids"] else 0)