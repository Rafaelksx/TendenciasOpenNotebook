import streamlit as st
from src.db import get_vector_collection
from src.config import SVG_FILE

# --- CSS---
EXPLORER_GLASS_CSS = '''
<style>
/* Tarjetas principales de los documentos */
.doc-glass-card {
    background: rgba(255, 255, 255, 0.4) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.6) !important;
    border-radius: 16px !important;
    padding: 16px 24px !important;
    margin-bottom: 5px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
    transition: transform 0.2s ease, background 0.3s ease;
    display: flex; 
    align-items: center; 
    gap: 16px;
}

.doc-glass-card:hover {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.6) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05) !important;
}

/* Tipografía dentro de las tarjetas */
.doc-title { 
    color: #0f172a !important; /* Azul marino oscuro */
    font-size: 1.15rem; 
    font-weight: 700; 
    margin: 0; 
    font-family: 'Inter', sans-serif;
}

.doc-subtitle { 
    color: #475569 !important; /* Gris pizarra */
    font-size: 0.85rem; 
    margin: 4px 0 0 0; 
    font-weight: 500;
}

/* Cajas expansibles de los fragmentos (Chunks) */
.glass-chunk-box {
    background: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px;
    padding: 16px;
    margin-top: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
}

.glass-chunk-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-weight: 800;
    color: #0047ff !important; /* Acento azul eléctrico */
    font-size: 0.9rem;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    padding-bottom: 6px;
}

.glass-chunk-text {
    margin: 0;
    line-height: 1.6;
    color: #334155 !important; /* Gris muy oscuro para lectura cómoda */
    font-size: 0.9rem;
}
</style>
'''

def render():
    # Inyectar el CSS visual al renderizar la vista
    st.markdown(EXPLORER_GLASS_CSS, unsafe_allow_html=True)
    
    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)
    
    all_metadata = collection.get()
    ingested_docs = list(set([m["source"] for m in all_metadata["metadatas"]])) if all_metadata and all_metadata["metadatas"] else []

    st.markdown("<h3 style='color: #0f172a;'>Documentos Ingeridos en la Base Vectorial</h3>", unsafe_allow_html=True)
    
    if len(ingested_docs) == 0:
        st.info("Aún no has cargado ningún documento. Sube archivos en la pestaña 'Cargar Archivos'.")
    else:
        for idx, doc_name in enumerate(ingested_docs):
            with st.container():
                col_doc, col_btn = st.columns([0.88, 0.12])
                with col_doc:
                    st.markdown(f"""
<div class="doc-glass-card">
    <div>{SVG_FILE}</div>
    <div style="flex-grow: 1;">
        <h4 class="doc-title">{doc_name}</h4>
        <p class="doc-subtitle">Origen local indexado en volumen persistente</p>
    </div>
</div>
""", unsafe_allow_html=True)
                with col_btn:
                    st.write("") 
                    st.write("")
                    if st.button("🗑️", key=f"del_doc_{doc_name}_{idx}", help=f"Eliminar {doc_name} de esta conversación"):
                        collection.delete(where={"source": doc_name})
                        st.session_state.pop(f"processed_{doc_name}", None)
                        st.success(f"¡Documento '{doc_name}' eliminado!")
                        st.rerun()
                
                with st.expander(f"Ver fragmentos indexados de {doc_name}"):
                    doc_chunks = collection.get(where={"source": doc_name})
                    if doc_chunks and doc_chunks["documents"]:
                        for i, (chunk_text, meta) in enumerate(zip(doc_chunks["documents"], doc_chunks["metadatas"])):
                            st.markdown(f"""
                            <div class="glass-chunk-box">
                                <div class="glass-chunk-header">
                                    <span>Fragmento #{i+1}</span>
                                    <span>Página {meta['page']}</span>
                                </div>
                                <p class="glass-chunk-text">{chunk_text}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("No se encontraron fragmentos para este documento.")