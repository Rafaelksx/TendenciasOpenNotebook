import streamlit as st
import os
import requests
import json
from src.config import (
    OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL, DATA_DIR,
    SVG_LOGO, SVG_GEAR, SVG_STATS, SVG_FILE, SVG_STUDENT, SVG_TEACHER,
    CUSTOM_CSS
)
from src.db import get_vector_collection
from src.models import test_ollama_connection, get_installed_models, get_ollama_embedding
from src.parser import ingest_document
from src.history import get_chat_sessions, load_chat_session, save_chat_session, delete_chat_session

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Open Notebook - RAG Local",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales personalizados
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO ---
if "llm_model" not in st.session_state:
    st.session_state.llm_model = LLM_MODEL

if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = EMBEDDING_MODEL

if "current_session_id" not in st.session_state:
    import time
    st.session_state.current_session_id = f"session_{int(time.time())}"

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_session(st.session_state.current_session_id)

# Obtener colección vectorial de ChromaDB específica para esta conversación
collection_name = f"coll_{st.session_state.current_session_id}"
collection = get_vector_collection(collection_name)

# --- ESTADO DE CONEXIONES Y PANEL LATERAL ---
st.sidebar.markdown(f"<h2 style='text-align: left; color: #f8fafc; font-weight: 600; font-size: 1.4rem;'>{SVG_GEAR}Panel de Control</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

ollama_connected = test_ollama_connection()
installed_models = get_installed_models() if ollama_connected else []

if ollama_connected:
    st.sidebar.markdown(
        '<div class="status-container"><span class="status-dot active"></span>Ollama Conectado</div>',
        unsafe_allow_html=True
    )
    st.sidebar.markdown(f"**Dirección:** `{OLLAMA_BASE_URL}`")
    
    st.sidebar.markdown("<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:8px;'>Modelos Seleccionados</p>", unsafe_allow_html=True)
    
    # Selector de LLM
    llm_options = installed_models if installed_models else [LLM_MODEL]
    default_llm_idx = 0
    if st.session_state.llm_model in llm_options:
        default_llm_idx = llm_options.index(st.session_state.llm_model)
    elif LLM_MODEL in llm_options:
        default_llm_idx = llm_options.index(LLM_MODEL)
        
    st.session_state.llm_model = st.sidebar.selectbox(
        "Modelo de Lenguaje (LLM):",
        options=llm_options,
        index=default_llm_idx
    )
    
    # Selector de Embeddings
    emb_options = installed_models if installed_models else [EMBEDDING_MODEL]
    default_emb_idx = 0
    if st.session_state.embedding_model in emb_options:
        default_emb_idx = emb_options.index(st.session_state.embedding_model)
    elif EMBEDDING_MODEL in emb_options:
        default_emb_idx = emb_options.index(EMBEDDING_MODEL)
        
    st.session_state.embedding_model = st.sidebar.selectbox(
        "Modelo de Embeddings:",
        options=emb_options,
        index=default_emb_idx
    )
    
    # Descargar nuevo modelo
    st.sidebar.markdown("<p style='font-size:0.85rem; font-weight:600; color:#94a3b8; margin-top:10px; margin-bottom:5px;'>Descargar Nuevo Modelo</p>", unsafe_allow_html=True)
    model_to_pull = st.sidebar.text_input("Nombre del modelo (ej: llama3, gemma2):", key="pull_model_input_sidebar")
    if st.sidebar.button("Descargar Modelo", use_container_width=True):
        if model_to_pull:
            with st.sidebar.spinner(f"Descargando '{model_to_pull}'..."):
                try:
                    pull_url = f"{OLLAMA_BASE_URL}/api/pull"
                    payload = {"name": model_to_pull.strip(), "stream": False}
                    response = requests.post(pull_url, json=payload, timeout=600)
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
    st.sidebar.markdown(
        '<div class="status-container"><span class="status-dot inactive"></span>Ollama Desconectado</div>',
        unsafe_allow_html=True
    )
    st.sidebar.error("Sin comunicación con el servidor Ollama.")
    st.sidebar.info(
        f"Asegúrate de que Ollama está activo en {OLLAMA_BASE_URL} y los modelos estén descargados."
    )
    if st.sidebar.button("Reintentar Conexión"):
        st.rerun()

# --- AJUSTES RAG ---
st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>Configuración del RAG</p>", unsafe_allow_html=True)
rag_k = st.sidebar.slider(
    "Número de fragmentos (k):",
    min_value=1,
    max_value=10,
    value=4,
    step=1,
    help="Número de fragmentos de texto recuperados de la base de datos para responder a la pregunta."
)

similarity_threshold = st.sidebar.slider(
    "Umbral de Similitud Mínimo:",
    min_value=0.0,
    max_value=1.0,
    value=0.2,
    step=0.05,
    help="Umbral de similitud (1 - distancia coseno) mínimo requerido para considerar un fragmento relevante."
)

# --- HISTORIAL DE CONVERSACIONES ---
st.sidebar.markdown("---")
st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>Historial de Chats</p>", unsafe_allow_html=True)

if st.sidebar.button("📝 Nueva Conversación", use_container_width=True):
    import time
    new_sess_id = f"session_{int(time.time())}"
    st.session_state.current_session_id = new_sess_id
    st.session_state.messages = []
    st.rerun()

sessions = get_chat_sessions()
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
        st.session_state.messages = load_chat_session(selected_sess)
        st.rerun()
        
    if st.sidebar.button("🗑️ Eliminar Chat Actual", use_container_width=True):
        from src.db import get_chroma_client
        chroma_client = get_chroma_client()
        try:
            chroma_client.delete_collection(name=f"coll_{st.session_state.current_session_id}")
        except Exception:
            pass
            
        delete_chat_session(st.session_state.current_session_id)
        import time
        new_sess_id = f"session_{int(time.time())}"
        st.session_state.current_session_id = new_sess_id
        st.session_state.messages = []
        st.success("Conversación eliminada.")
        st.rerun()

st.sidebar.markdown("---")

# Estadísticas de la Base de Datos Vectorial
all_metadata = collection.get()
ingested_docs = list(set([m["source"] for m in all_metadata["metadatas"]])) if all_metadata and all_metadata["metadatas"] else []
total_indexed_chunks = len(all_metadata["ids"]) if all_metadata and all_metadata["ids"] else 0

st.sidebar.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#94a3b8; margin-bottom:12px;'>{SVG_STATS}Estadísticas RAG</p>", unsafe_allow_html=True)
st.sidebar.metric(label="Documentos Indexados", value=len(ingested_docs))
st.sidebar.metric(label="Total Chunks", value=total_indexed_chunks)
st.sidebar.caption(f"Dimensión Vectorial: 256 (Matryoshka normalizado)")

if len(ingested_docs) > 0:
    st.sidebar.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("Vaciar Base de Datos", use_container_width=True):
        from src.db import get_chroma_client
        chroma_client = get_chroma_client()
        chroma_client.delete_collection(name=collection_name)
        st.sidebar.success("Base de datos vaciada con éxito.")
        st.rerun()

# --- VISTA PRINCIPAL ---
st.markdown(f"""
<div class="brand-container">
{SVG_LOGO}
<h1 class="gradient-text">Open Notebook</h1>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="gradient-subtitle">Libreta inteligente local RAG • Privacidad absoluta y desconexión de red</div>', unsafe_allow_html=True)

# Pestañas para organizar el contenido
tab_chat, tab_explorer, tab_upload = st.tabs(["Chat de Consulta", "Explorador de Documentos", "Cargar Archivos"])

# --- PESTAÑA: CARGAR ARCHIVOS ---
with tab_upload:
    st.markdown("### Ingesta de Literatura Científica y Material de Estudio")
    st.write("Sube tus libros, artículos o apuntes para procesar, fragmentar y almacenar de forma segura y local.")
    
    uploaded_files = st.file_uploader(
        "Elige archivos PDF, Word o TXT para añadir a la base de conocimiento:",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_key = f"processed_{uploaded_file.name}"
            if file_key not in st.session_state:
                file_bytes = uploaded_file.read()
                success = ingest_document(collection, uploaded_file.name, file_bytes, uploaded_file.type)
                if success:
                    st.session_state[file_key] = True
                    st.rerun()

# --- PESTAÑA: EXPLORADOR DE DOCUMENTOS ---
with tab_explorer:
    st.markdown("### Documentos Ingeridos en la Base Vectorial")
    if len(ingested_docs) == 0:
        st.info("Aún no has cargado ningún documento. Sube archivos en la pestaña 'Cargar Archivos'.")
    else:
        for idx, doc_name in enumerate(ingested_docs):
            with st.container():
                col_doc, col_btn = st.columns([0.88, 0.12])
                with col_doc:
                    st.markdown(f"""
<div class="card" style="display: flex; align-items: center; gap: 12px; padding: 16px 24px; margin-bottom: 5px;">
{SVG_FILE}
<div style="flex-grow: 1;">
<h4 style="margin: 0; color: #f8fafc; font-size: 1.1rem;">{doc_name}</h4>
<p style="color:#94a3b8; font-size: 0.8rem; margin: 2px 0 0 0;">Origen local indexado en volumen persistente</p>
</div>
</div>
""", unsafe_allow_html=True)
                with col_btn:
                    st.write("") # Espacio para centrar verticalmente
                    st.write("")
                    if st.button("🗑️", key=f"del_doc_{doc_name}_{idx}", help=f"Eliminar {doc_name} de esta conversación"):
                        # Eliminar de ChromaDB
                        collection.delete(where={"source": doc_name})
                        # Limpiar flag de procesado
                        st.session_state.pop(f"processed_{doc_name}", None)
                        st.success(f"¡Documento '{doc_name}' eliminado!")
                        st.rerun()
                
                with st.expander(f"Ver fragmentos indexados de {doc_name}"):
                    doc_chunks = collection.get(where={"source": doc_name})
                    if doc_chunks and doc_chunks["documents"]:
                        for i, (chunk_text, meta) in enumerate(zip(doc_chunks["documents"], doc_chunks["metadatas"])):
                            st.markdown(f"""
<div class="chunk-box">
<div class="chunk-header">
<span>Fragmento #{i+1}</span>
<span>Página {meta['page']}</span>
</div>
<p style="margin: 0; line-height: 1.5; color: #cbd5e1;">{chunk_text}</p>
</div>
""", unsafe_allow_html=True)
                    else:
                        st.write("No se encontraron fragmentos para este documento.")

# --- PESTAÑA: CHAT DE CONSULTA (RAG) ---
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "active_query" not in st.session_state:
        st.session_state.active_query = None

    # Plantillas de tareas rápidas
    st.markdown("### Tareas Rápidas Inteligentes")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<p style='font-weight:600; color:#818cf8; margin-bottom:12px; font-size: 1rem;'>{SVG_STUDENT}Para Estudiantes</p>", unsafe_allow_html=True)
        btn_summary = st.button("Sintetizar material principal", use_container_width=True, help="Generar un resumen ejecutivo del material cargado.")
        btn_quiz = st.button("Generar un simulacro de examen", use_container_width=True, help="Crear 5 preguntas de opción múltiple basadas en los textos.")
        btn_formulas = st.button("Extraer metodologías y fórmulas clave", use_container_width=True, help="Extraer y explicar las fórmulas del texto indexado.")
        
        if btn_summary:
            st.session_state.active_query = "Realiza un resumen estructurado, analítico y conciso de los conceptos principales expuestos en los documentos suministrados."
        elif btn_quiz:
            st.session_state.active_query = "Crea un cuestionario/simulacro de examen con 5 preguntas complejas sobre el material indexado, con sus respuestas justificadas."
        elif btn_formulas:
            st.session_state.active_query = "Extrae de forma ordenada todas las metodologías, metodologías matemáticas, fórmulas o algoritmos clave explicados en el texto."
            
    with col2:
        st.markdown(f"<p style='font-weight:600; color:#c084fc; margin-bottom:12px; font-size: 1rem;'>{SVG_TEACHER}Para Docentes e Investigadores</p>", unsafe_allow_html=True)
        btn_thesis = st.button("Revisar estructura de borrador de tesis", use_container_width=True, help="Evaluar la consistencia y estructura de los textos presentados.")
        btn_syllabus = st.button("Diseñar syllabus y asignaciones académicas", use_container_width=True, help="Proponer temarios y actividades programáticas basadas en el contenido.")
        btn_review = st.button("Evaluación ciega de artículos científicos", use_container_width=True, help="Analizar debilidades metodológicas y de rigor científico.")
        
        if btn_thesis:
            st.session_state.active_query = "Evalúa críticamente la coherencia metodológica, la estructura académica y la consistencia teórica en base a la bibliografía cargada."
        elif btn_syllabus:
            st.session_state.active_query = "Diseña una propuesta pedagógica (syllabus) de 4 unidades didácticas y 2 actividades de evaluación basadas directamente en este material."
        elif btn_review:
            st.session_state.active_query = "Realiza una revisión ciega del material: identifica fortalezas, debilidades metodológicas y sugerencias de mejora del rigor científico."

    st.markdown("---")

    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "retrieved_chunks" in message and message["retrieved_chunks"]:
                with st.expander("Ver fuentes de contexto utilizadas para esta respuesta"):
                    for idx, chunk in enumerate(message["retrieved_chunks"]):
                        st.markdown(f"""
<div class="chunk-box">
<div class="chunk-header">
<span>{chunk['source']} (Pág. {chunk['page']})</span>
<span>Similitud: {chunk['score']:.4f}</span>
</div>
<p style='margin:0; font-size:0.85rem; color:#cbd5e1;'>{chunk['text']}</p>
</div>
""", unsafe_allow_html=True)

    user_query = st.chat_input("Realiza una pregunta sobre tus documentos indexados...")
    
    if st.session_state.active_query:
        user_query = st.session_state.active_query
        st.session_state.active_query = None
        
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        save_chat_session(st.session_state.current_session_id, st.session_state.messages)
        with st.chat_message("user"):
            st.markdown(user_query)
            
        retrieved_chunks_for_message = []
        context = ""
        
        if total_indexed_chunks > 0:
            with st.spinner("Buscando en la base de datos vectorial local..."):
                query_emb = get_ollama_embedding(user_query, "search_query: ")
                if query_emb:
                    results = collection.query(
                        query_embeddings=[query_emb],
                        n_results=min(rag_k, total_indexed_chunks)
                    )
                    
                    if results and results["documents"] and results["documents"][0]:
                        docs = results["documents"][0]
                        metas = results["metadatas"][0]
                        distances = results["distances"][0] if "distances" in results else [0.5]*len(docs)
                        
                        context_parts = []
                        for idx, (doc_text, meta, dist) in enumerate(zip(docs, metas, distances)):
                            similarity_score = 1.0 - dist
                            if similarity_score >= similarity_threshold:
                                retrieved_chunks_for_message.append({
                                    "text": doc_text,
                                    "source": meta["source"],
                                    "page": meta["page"],
                                    "score": similarity_score
                                })
                                context_parts.append(
                                    f"[Fuente: {meta['source']}, Pág: {meta['page']}]\n{doc_text}"
                                )
                        context = "\n\n---\n\n".join(context_parts)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            system_prompt = (
                "Eres Open Notebook, un copiloto académico de inteligencia artificial basado en RAG.\n"
                "Tu objetivo es ayudar a estudiantes y docentes respondiendo a sus preguntas basándote estrictamente en el contexto proveído.\n"
                "Reglas críticas:\n"
                "1. Si el contexto provisto es relevante, redacta una respuesta clara, analítica y detallada citando las fuentes y páginas correspondientes.\n"
                "2. Si el contexto no contiene la información para responder la pregunta, di honestamente que los documentos suministrados no contienen dicha información, pero no alucines ni inventes respuestas.\n"
                "3. Mantén un tono formal, educativo y profesional.\n"
            )
            
            user_prompt = f"Contexto Suministrado:\n{context}\n\nPregunta: {user_query}"
            
            if not ollama_connected:
                full_response = "Error: El servicio Ollama está fuera de línea. Por favor, verifica el Panel de Control lateral."
                message_placeholder.markdown(full_response)
            else:
                url = f"{OLLAMA_BASE_URL}/api/chat"
                payload = {
                    "model": st.session_state.get("llm_model", LLM_MODEL),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": True
                }
                
                try:
                    st.write("") # Margen estético para el texto en streaming
                    response = requests.post(url, json=payload, stream=True, timeout=60)
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line:
                            line_data = json.loads(line.decode("utf-8"))
                            chunk_msg = line_data.get("message", {}).get("content", "")
                            full_response += chunk_msg
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Error de comunicación con Ollama: {e}"
                    message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "retrieved_chunks": retrieved_chunks_for_message
            })
            save_chat_session(st.session_state.current_session_id, st.session_state.messages)
            
            st.rerun()
