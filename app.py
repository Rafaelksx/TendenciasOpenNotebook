import streamlit as st
import os
import requests
import json
import numpy as np
from pypdf import PdfReader
import chromadb
from chromadb.config import Settings

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Open Notebook - RAG Local",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VARIABLES DE ENTORNO Y CONFIGURACIÓN ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Crear directorio de datos si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Crear directorio para almacenar el historial de chat
HISTORY_DIR = os.path.join(DATA_DIR, "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_chat_sessions():
    sessions = []
    if os.path.exists(HISTORY_DIR):
        for f in os.listdir(HISTORY_DIR):
            if f.endswith(".json"):
                session_id = f[:-5]
                filepath = os.path.join(HISTORY_DIR, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        display_name = "Conversación vacía"
                        for msg in data:
                            if msg.get("role") == "user":
                                display_name = msg.get("content")[:30]
                                if len(msg.get("content")) > 30:
                                    display_name += "..."
                                break
                        mtime = os.path.getmtime(filepath)
                        sessions.append((session_id, display_name, mtime))
                except Exception:
                    pass
    sessions.sort(key=lambda x: x[2], reverse=True)
    return [(s[0], s[1]) for s in sessions]

def load_chat_session(session_id):
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_chat_session(session_id, messages):
    if not messages:
        return
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error guardando sesión de chat: {e}")

def delete_chat_session(session_id):
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass

# --- SVG ICONS CONSTANTS ---
SVG_LOGO = """
<svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="url(#brand-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 12px;">
  <defs>
    <linearGradient id="brand-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a78bfa" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>
  </defs>
  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
</svg>
"""

SVG_GEAR = """
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
  <circle cx="12" cy="12" r="3"/>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
</svg>
"""

SVG_STATS = """
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
  <line x1="18" y1="20" x2="18" y2="10"/>
  <line x1="12" y1="20" x2="12" y2="4"/>
  <line x1="6" y1="20" x2="6" y2="14"/>
</svg>
"""

SVG_FILE = """
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
  <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
  <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
  <path d="M10 9H8"/>
  <path d="M16 13H8"/>
  <path d="M16 17H8"/>
</svg>
"""

SVG_STUDENT = """
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
  <path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>
  <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/>
</svg>
"""

SVG_TEACHER = """
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
  <path d="M2 3h20"/>
  <path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/>
  <path d="m7 21 5-5 5 5"/>
</svg>
"""
# --- DISEÑO DE INTERFAZ PREMIUM (CUSTOM CSS) ---
st.markdown("""
<style>

/* Degradado en el título principal */
.brand-container {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
}

.gradient-text {
    background: linear-gradient(135deg, #a78bfa 0%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.8rem;
    letter-spacing: -0.04em;
    margin: 0;
}

.gradient-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* Estilos de tarjetas y secciones */
.card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    border-color: #6366f1;
}

/* Estilo de los Chunks recuperados */
.chunk-box {
    background-color: #0f172a;
    border-left: 4px solid #6366f1;
    border-radius: 4px 12px 12px 4px;
    padding: 12px 16px;
    margin-bottom: 12px;
    font-size: 0.9rem;
}

.chunk-header {
    font-size: 0.8rem;
    color: #818cf8;
    font-weight: 600;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
}

/* Indicador de conexión con pulsación */
.status-container {
    display: inline-flex;
    align-items: center;
    background-color: #0f172a;
    border: 1px solid #334155;
    padding: 6px 16px;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 15px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 10px;
}

.status-dot.active {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse-green 2s infinite;
}

.status-dot.inactive {
    background-color: #ef4444;
    box-shadow: 0 0 8px #ef4444;
    animation: pulse-red 2s infinite;
}

@keyframes pulse-green {
    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes pulse-red {
    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* Configuración visual de los Chat Bubbles */
.stChatMessage {
    border-radius: 16px !important;
    padding: 14px 20px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 2px 4px rgb(0 0 0 / 0.05);
}

/* Ajustes específicos en elementos interactivos */
div[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

.stButton > button {
    border-radius: 10px !important;
    transition: all 0.2s ease-in-out !important;
    font-weight: 500 !important;
}

.stButton > button:hover {
    border-color: #818cf8 !important;
    color: #818cf8 !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


# --- CLIENTE CHROMADB ---
@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma"))

chroma_client = get_chroma_client()
collection_name = "open_notebook_docs"

try:
    collection = chroma_client.get_collection(name=collection_name)
except Exception:
    collection = chroma_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


# --- FUNCIONES DE INTEGRACIÓN CON OLLAMA ---

def test_ollama_connection():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

def get_installed_models():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            return [m["name"] for m in models_data]
    except Exception:
        pass
    return []

def get_ollama_embedding(text, prefix):
    full_text = f"{prefix}{text}"
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": st.session_state.get("embedding_model", EMBEDDING_MODEL),
        "prompt": full_text
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        full_embedding = response.json()["embedding"]
        
        # --- MATRYOSHKA LEARNING REDUCTION (Truncamiento a 256 dimensiones) ---
        truncated_embedding = full_embedding[:256]
        
        # --- NORMALIZACIÓN L2 ---
        vec = np.array(truncated_embedding)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
            
        return vec.tolist()
    except Exception as e:
        st.error(f"Error generando embedding para el fragmento: {e}")
        return None


# --- PROCESAMIENTO Y FRAGMENTACIÓN DE DOCUMENTOS ---

def recursive_split_text(text, chunk_size, chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""]):
    if len(text) <= chunk_size:
        return [text]
    
    separator = separators[-1]
    for sep in separators:
        if sep in text:
            separator = sep
            break
            
    splits = text.split(separator)
    chunks = []
    current_chunk = ""
    
    for split in splits:
        if len(current_chunk) + len(split) + len(separator) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                current_chunk = current_chunk[-chunk_overlap:] + separator + split
            else:
                current_chunk = split
        else:
            if current_chunk:
                current_chunk += separator + split
            else:
                current_chunk = split
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    final_chunks = []
    next_separators = [s for s in separators if s != separator]
    if not next_separators:
        next_separators = [""]
        
    for chunk in chunks:
        if len(chunk) > chunk_size:
            final_chunks.extend(recursive_split_text(chunk, chunk_size, chunk_overlap, next_separators))
        else:
            final_chunks.append(chunk)
            
    return [c for c in final_chunks if len(c.strip()) > 10]

def extract_text_from_docx(file_bytes):
    from io import BytesIO
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return [{"text": "\n\n".join(full_text), "page": 1}]

def extract_text_from_pdf(file_bytes):
    from io import BytesIO
    pdf_reader = PdfReader(BytesIO(file_bytes))
    pages_content = []
    for i, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text:
            pages_content.append({"text": text, "page": i + 1})
    return pages_content

def chunk_pages(pages_content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    for item in pages_content:
        text = item["text"]
        page_num = item["page"]
        
        split_chunks = recursive_split_text(text, chunk_size, overlap)
        for chunk_text in split_chunks:
            chunks.append({
                "text": chunk_text,
                "page": page_num
            })
    return chunks

def ingest_document(filename, file_bytes, file_type):
    with st.spinner(f"Procesando e indexando '{filename}'..."):
        if file_type == "application/pdf":
            pages = extract_text_from_pdf(file_bytes)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith(".docx"):
            pages = extract_text_from_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            pages = [{"text": text, "page": 1}]
            
        if not pages:
            st.error("No se pudo extraer texto del documento.")
            return False
            
        chunks = chunk_pages(pages)
        if not chunks:
            st.error("No se generaron fragmentos válidos del documento.")
            return False
            
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        progress_bar = st.progress(0, text="Generando embeddings de alta calidad (Matryoshka 256d)...")
        total_chunks = len(chunks)
        
        for idx, chunk in enumerate(chunks):
            emb = get_ollama_embedding(chunk["text"], "search_document: ")
            if emb is None:
                st.error("Error al comunicarse con el modelo de embeddings. Asegúrate de tener Ollama activo.")
                return False
                
            chunk_id = f"{filename}_ch_{idx}"
            ids.append(chunk_id)
            embeddings.append(emb)
            documents.append(chunk["text"])
            metadatas.append({
                "source": filename,
                "page": chunk["page"],
                "index": idx
            })
            
            progress_bar.progress((idx + 1) / total_chunks, text=f"Indexado fragmento {idx + 1} de {total_chunks}")
            
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        st.success(f"Ingerido '{filename}' con {len(chunks)} fragmentos indexados correctamente.")
        return True


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

# --- ESTADO DE CONEXIONES Y PANEL LATERAL ---

st.sidebar.markdown(f"<h2 style='text-align: left; color: #f8fafc; font-weight: 600; font-size: 1.4rem;'>{SVG_GEAR}Panel de Control</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Verificaciones de Ollama
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

# Botón para crear una conversación nueva
if st.sidebar.button("📝 Nueva Conversación", use_container_width=True):
    import time
    new_sess_id = f"session_{int(time.time())}"
    st.session_state.current_session_id = new_sess_id
    st.session_state.messages = []
    st.rerun()

sessions = get_chat_sessions()
if sessions:
    # Mapear ids a nombres para el dropdown
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
        chroma_client.delete_collection(name=collection_name)
        st.sidebar.success("Base de datos vaciada con éxito.")
        st.rerun()


# --- VISTA PRINCIPAL ---

# Título y encabezado premium sin emojis obsoletos, utilizando SVG
st.markdown(f"""
<div class="brand-container">
{SVG_LOGO}
<h1 class="gradient-text">Open Notebook</h1>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="gradient-subtitle">Libreta inteligente local RAG • Privacidad absoluta y desconexión de red</div>', unsafe_allow_html=True)

# Pestañas para organizar el contenido (sin emojis)
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
                success = ingest_document(uploaded_file.name, file_bytes, uploaded_file.type)
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
                st.markdown(f"""
<div class="card" style="display: flex; align-items: center; gap: 12px; padding: 16px 24px;">
{SVG_FILE}
<div style="flex-grow: 1;">
<h4 style="margin: 0; color: #f8fafc; font-size: 1.1rem;">{doc_name}</h4>
<p style="color:#94a3b8; font-size: 0.8rem; margin: 2px 0 0 0;">Origen local indexado en volumen persistente</p>
</div>
</div>
""", unsafe_allow_html=True)
                
                # Permitir ver chunks del documento
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

    # Plantillas de tareas rápidas (Quick Action Cards)
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

    # Mostrar historial de mensajes de chat
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
