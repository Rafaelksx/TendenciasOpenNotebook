import streamlit as st
import requests
from src.db import get_vector_collection
from src.parser import ingest_document

def render():
    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)

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

    st.markdown("---")
    st.markdown("### 🌐 Investigar e Ingestar desde la Web")
    st.write("Escribe un término de búsqueda para buscar en la web ( DuckDuckGo / Wikipedia ) o pega una dirección (URL) directa para extraer su información.")
    
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