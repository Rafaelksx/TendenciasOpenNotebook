import streamlit as st
from src.db import get_vector_collection
from src.parser import ingest_document

def render():
    collection_name = f"coll_{st.session_state.current_session_id}"
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