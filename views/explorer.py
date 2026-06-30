import streamlit as st
from src.db import get_vector_collection
from src.config import SVG_FILE

def render():
    usuario_id = st.session_state['usuario']['id']
    collection_name = f"coll_{usuario_id}_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)
    
    all_metadata = collection.get()
    ingested_docs = list(set([m["source"] for m in all_metadata["metadatas"]])) if all_metadata and all_metadata["metadatas"] else []

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