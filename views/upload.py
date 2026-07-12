import streamlit as st
import requests
from src.db import get_vector_collection
from src.parser import ingest_document

# --- CSS ---
UPLOAD_GLASS_CSS = '''
<style>
/* Titulos y textos descriptivos */
.upload-title {
    color: #0f172a !important;
    font-weight: 800;
    font-size: 1.5rem;
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
}
.upload-subtitle {
    color: #475569 !important;
    font-weight: 500;
    font-size: 0.95rem;
    margin-bottom: 25px;
}

/* Glassmorfismo para la zona de Arrastrar y soltar archivos */
[data-testid="stFileUploadDropzone"] {
    background: rgba(255, 255, 255, 0.25) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 2px dashed rgba(0, 71, 255, 0.3) !important;
    border-radius: 20px !important;
    padding: 2.5rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    background: rgba(255, 255, 255, 0.4) !important;
    border-color: #ec4899 !important; /* Cambio a rosa al pasar el mouse */
    box-shadow: 0 8px 24px rgba(236, 72, 153, 0.1) !important;
}

[data-testid="stFileUploadDropzone"] * {
    color: #0f172a !important; /* Forzar iconos y texto a color oscuro */
}

/* Estilo de los archivos subidos y la barra de carga */
[data-testid="stUploadedFile"] {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(236, 72, 153, 0.2) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
}

/* Texto indicador (Label) encima de la barra de progreso */
[data-testid="stProgress"] label {
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    background: transparent !important; 
    padding-bottom: 6px !important;
}

/* Fondo de la barra de progreso (Track) */
[data-testid="stProgress"] > div:last-child > div {
    background: rgba(226, 232, 240, 0.8) !important; 
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
    border-radius: 10px !important;
    height: 12px !important; 
}

/* Relleno de la barra de progreso (Fill) */
[data-testid="stProgress"] [role="progressbar"] {
    background: linear-gradient(90deg, #8b5cf6 0%, #ec4899 100%) !important; 
    border-radius: 10px !important;
    height: 12px !important;
    box-shadow: 0 0 8px rgba(236, 72, 153, 0.4) !important; 
}

/*Formulario de busqueda web */
div[data-testid="stForm"] {
    max-width: 100% !important;
    margin: 10px 0 !important;
    padding: 2rem !important;
    background: rgba(15, 23, 42, 0.04) !important; 
    backdrop-filter: blur(12px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(15, 23, 42, 0.08) !important; 
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.02) !important; /* Efecto hundido */
}

div[data-testid="stForm"] input {
    background: rgba(255, 255, 255, 0.9) !important; 
    border: 1px solid rgba(0, 71, 255, 0.3) !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}

div[data-testid="stForm"] input:focus {
    background: #ffffff !important;
    border-color: #8b5cf6 !important; 
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
}
</style>
'''

def render():
    st.markdown(UPLOAD_GLASS_CSS, unsafe_allow_html=True)
    
    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)

    st.markdown("<h3 class='upload-title'>Ingesta de Material de Estudio</h3>", unsafe_allow_html=True)
    st.markdown("<p class='upload-subtitle'>Sube tus libros, artículos o apuntes para procesar, fragmentar y almacenar de forma segura y local.</p>", unsafe_allow_html=True)
    
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

    st.markdown("<br><hr style='border-color: rgba(0,0,0,0.05);'><br>", unsafe_allow_html=True)
    
    st.markdown("<h3 class='upload-title'>🌐 Investigar e Ingestar desde la Web</h3>", unsafe_allow_html=True)
    st.markdown("<p class='upload-subtitle'>Escribe un término de búsqueda para buscar en la web ( DuckDuckGo / Wikipedia ) o pega una dirección (URL) directa para extraer su información.</p>", unsafe_allow_html=True)
    
    with st.form("web_research_form"):
        search_query = st.text_input("Palabra clave o enlace URL (ej: 'Matryoshka embeddings' o 'https://concepto.de/ciclo-del-agua/'):")
        submit_search = st.form_submit_button("Buscar e Ingestar")
        
        if submit_search and search_query:
            query_stripped = search_query.strip()
            is_url = query_stripped.startswith(("http://", "https://"))
            
            with st.spinner("Procesando URL o buscando en internet..."):
                try:
                    from bs4 import BeautifulSoup
                    import re
                    
                    content = []
                    filename = ""
                    
                    # Definimos un User-Agent común para evitar bloqueos 403 en Wikipedia y otras webs
                    custom_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                    
                    if is_url:
                        # --- MODO 1: PROCESAR URL DIRECTA ---
                        url = query_stripped
                        try:
                            resp = requests.get(url, timeout=12, headers=custom_headers)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, "html.parser")
                                # Limpiar basura
                                for s in soup(["script", "style", "nav", "footer", "header", "aside"]):
                                    s.decompose()
                                text = soup.get_text(separator="\n")
                                cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
                                cleaned_text = "\n".join(cleaned_lines)
                                
                                page_title = soup.title.string.strip() if soup.title and soup.title.string else url.split("/")[-1] or "pagina_web"
                                content.append(f"=== FUENTE: {page_title} ({url}) ===")
                                content.append(cleaned_text)
                                
                                safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', page_title.lower())
                                filename = f"web_url_{safe_title[:50]}.txt"
                            else:
                                st.error(f"Error al acceder a la URL. Código de estado: {resp.status_code}")
                        except Exception as e:
                            st.error(f"No se pudo conectar a la URL: {e}")
                    else:
                        # --- MODO 2: BÚSQUEDA WEB (DuckDuckGo + Fallback Wikipedia) ---
                        from duckduckgo_search import DDGS
                        results = []
                        
                        # A. Buscar en DuckDuckGo
                        try:
                            with DDGS() as ddgs:
                                results = list(ddgs.text(query_stripped, max_results=4))
                                if not results and " " in query_stripped:
                                    query_alt = query_stripped.replace(" ", "+")
                                    results = list(ddgs.text(query_alt, max_results=4))
                        except Exception:
                            results = []
                            
                        if not results:
                            st.error("No se encontraron resultados en la web para esta palabra clave.")
                        else:
                            for r in results:
                                s_url = r.get("href")
                                s_title = r.get("title")
                                s_snippet = r.get("body")
                                
                                content.append(f"=== FUENTE: {s_title} ({s_url}) ===")
                                try:
                                    resp = requests.get(s_url, timeout=5, headers=custom_headers)
                                    if resp.status_code == 200:
                                        soup = BeautifulSoup(resp.text, "html.parser")
                                        for s in soup(["script", "style", "nav", "footer", "header", "aside"]):
                                            s.decompose()
                                        text = soup.get_text(separator="\n")
                                        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
                                        cleaned_text = "\n".join(cleaned_lines[:150])
                                        content.append(cleaned_text)
                                    else:
                                        content.append(s_snippet)
                                except Exception:
                                    content.append(s_snippet)
                                    
                            safe_query = re.sub(r'[^a-zA-Z0-9_]', '_', query_stripped.lower())
                            filename = f"web_investigacion_{safe_query[:50]}.txt"
                            
                    if content and filename:
                        final_text = "\n\n".join(content)
                        success = ingest_document(collection, filename, final_text.encode("utf-8"), "text/plain")
                        if success:
                            st.success(f"¡Ingesta exitosa del documento '{filename}'!")
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Error durante el procesamiento: {e}")