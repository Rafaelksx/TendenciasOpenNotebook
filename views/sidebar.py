import streamlit as st
import requests
import time
from src.config import OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL, SVG_GEAR, SVG_STATS
from src.db import get_vector_collection, get_chroma_client
from src.models import test_ollama_connection, get_installed_models
from src.history import get_chat_sessions, load_chat_session, delete_chat_session

def render():
    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)

    st.sidebar.markdown(f"<h2 style='text-align: left; color: #f8fafc; font-weight: 600; font-size: 1.4rem;'>{SVG_GEAR}Panel de Control</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state['usuario'] = None
        st.session_state.messages = []
        st.query_params.clear()
        st.rerun()
# Botón de Cerrar Sesión justo al final del sidebar
    st.sidebar.markdown("---")



    ollama_connected = test_ollama_connection()
    installed_models = get_installed_models() if ollama_connected else []

    if ollama_connected:
        st.sidebar.markdown('<div class="status-container"><span class="status-dot active"></span>Ollama Conectado</div>', unsafe_allow_html=True)
        st.sidebar.markdown(f"**Dirección:** `{OLLAMA_BASE_URL}`")
        
        st.sidebar.markdown("<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:8px;'>Modelos Seleccionados</p>", unsafe_allow_html=True)
        
        llm_options = installed_models if installed_models else [LLM_MODEL]
        default_llm_idx = llm_options.index(st.session_state.llm_model) if st.session_state.llm_model in llm_options else (llm_options.index(LLM_MODEL) if LLM_MODEL in llm_options else 0)
            
        st.session_state.llm_model = st.sidebar.selectbox("Modelo de Lenguaje (LLM):", options=llm_options, index=default_llm_idx)
        
        emb_options = installed_models if installed_models else [EMBEDDING_MODEL]
        default_emb_idx = emb_options.index(st.session_state.embedding_model) if st.session_state.embedding_model in emb_options else (emb_options.index(EMBEDDING_MODEL) if EMBEDDING_MODEL in emb_options else 0)
            
        st.session_state.embedding_model = st.sidebar.selectbox("Modelo de Embeddings:", options=emb_options, index=default_emb_idx)
        
        st.sidebar.markdown("<p style='font-size:0.85rem; font-weight:600; color:#94a3b8; margin-top:10px; margin-bottom:5px;'>Descargar Nuevo Modelo</p>", unsafe_allow_html=True)
        model_to_pull = st.sidebar.text_input("Nombre del modelo (ej: llama3, gemma2):", key="pull_model_input_sidebar")
        
        if st.sidebar.button("Descargar Modelo", use_container_width=True):
            if model_to_pull:
                with st.sidebar.spinner(f"Descargando '{model_to_pull}'..."):
                    try:
                        pull_url = f"{OLLAMA_BASE_URL}/api/pull"
                        response = requests.post(pull_url, json={"name": model_to_pull.strip(), "stream": False}, timeout=600)
                        if response.status_code == 200:
                            st.sidebar.success(f"¡Modelo '{model_to_pull}' descargado!")
                            st.rerun()
                        else:
                            st.sidebar.error(f"Error al descargar: {response.text}")
                    except Exception as e:
                        st.sidebar.error(f"Error de conexión: {e}")
            else:
                st.sidebar.warning("Introduce un nombre de modelo.")
    else:
        st.sidebar.markdown('<div class="status-container"><span class="status-dot inactive"></span>Ollama Desconectado</div>', unsafe_allow_html=True)
        st.sidebar.error("Sin comunicación con el servidor Ollama.")
        if st.sidebar.button("Reintentar Conexión"):
            st.rerun()

    # --- AJUSTES RAG ---
    st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>Configuración del RAG</p>", unsafe_allow_html=True)
    st.session_state.rag_k = st.sidebar.slider("Número de fragmentos (k):", min_value=1, max_value=10, value=4, step=1)
    st.session_state.similarity_threshold = st.sidebar.slider("Umbral de Similitud Mínimo:", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    # --- HISTORIAL DE CONVERSACIONES ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>Historial de Chats</p>", unsafe_allow_html=True)

    if st.sidebar.button("📝 Nueva Conversación", use_container_width=True):
        st.session_state.current_session_id = f"session_{int(time.time())}"
        st.session_state.messages = []
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
            
        if st.sidebar.button("🗑️ Eliminar Chat Actual", use_container_width=True):
            chroma_client = get_chroma_client()
            try:
                chroma_client.delete_collection(name=collection_name)
            except Exception:
                pass
                
            delete_chat_session(usuario_id, st.session_state.current_session_id)
            st.session_state.current_session_id = f"session_{int(time.time())}"
            st.session_state.messages = []
            st.success("Conversación eliminada.")
            st.rerun()

    st.sidebar.markdown("---")

    # Estadísticas
    all_metadata = collection.get()
    ingested_docs = list(set([m["source"] for m in all_metadata["metadatas"]])) if all_metadata and all_metadata["metadatas"] else []
    total_indexed_chunks = len(all_metadata["ids"]) if all_metadata and all_metadata["ids"] else 0

    st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>{SVG_STATS}Estadísticas RAG</p>", unsafe_allow_html=True)
    st.sidebar.metric(label="Documentos Indexados", value=len(ingested_docs))
    st.sidebar.metric(label="Total Chunks", value=total_indexed_chunks)

    if len(ingested_docs) > 0:
        st.sidebar.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
        if st.sidebar.button("Vaciar Base de Datos", use_container_width=True):
            chroma_client = get_chroma_client()
            chroma_client.delete_collection(name=collection_name)
            st.sidebar.success("Base de datos vaciada con éxito.")
            st.rerun()