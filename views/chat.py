import streamlit as st
import requests
import json
from src.config import OLLAMA_BASE_URL, LLM_MODEL, SVG_STUDENT, SVG_TEACHER
from src.db import get_vector_collection
from src.models import test_ollama_connection, get_ollama_embedding
from src.history import save_chat_session

def render():
    collection_name = f"coll_{st.session_state.current_session_id}"
    collection = get_vector_collection(collection_name)
    
    all_metadata = collection.get()
    total_indexed_chunks = len(all_metadata["ids"]) if all_metadata and all_metadata["ids"] else 0
    ollama_connected = test_ollama_connection()

    if "active_query" not in st.session_state:
        st.session_state.active_query = None

    # Plantillas rápidas
    st.markdown("### Tareas Rápidas Inteligentes")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<p style='font-weight:600; color:#818cf8; margin-bottom:12px; font-size: 1rem;'>{SVG_STUDENT}Para Estudiantes</p>", unsafe_allow_html=True)
        if st.button("Sintetizar material principal", use_container_width=True): st.session_state.active_query = "Realiza un resumen estructurado, analítico y conciso de los conceptos principales expuestos en los documentos suministrados."
        if st.button("Generar un simulacro de examen", use_container_width=True): st.session_state.active_query = "Crea un cuestionario/simulacro de examen con 5 preguntas complejas sobre el material indexado, con sus respuestas justificadas."
        if st.button("Extraer metodologías y fórmulas clave", use_container_width=True): st.session_state.active_query = "Extrae de forma ordenada todas las metodologías, metodologías matemáticas, fórmulas o algoritmos clave explicados en el texto."
            
    with col2:
        st.markdown(f"<p style='font-weight:600; color:#c084fc; margin-bottom:12px; font-size: 1rem;'>{SVG_TEACHER}Para Docentes e Investigadores</p>", unsafe_allow_html=True)
        if st.button("Revisar estructura de borrador de tesis", use_container_width=True): st.session_state.active_query = "Evalúa críticamente la coherencia metodológica, la estructura académica y la consistencia teórica en base a la bibliografía cargada."
        if st.button("Diseñar syllabus y asignaciones académicas", use_container_width=True): st.session_state.active_query = "Diseña una propuesta pedagógica (syllabus) de 4 unidades didácticas y 2 actividades de evaluación basadas directamente en este material."
        if st.button("Evaluación ciega de artículos científicos", use_container_width=True): st.session_state.active_query = "Realiza una revisión ciega del material: identifica fortalezas, debilidades metodológicas y sugerencias de mejora del rigor científico."

    st.markdown("---")

    # Historial de mensajes
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
                    rag_k = st.session_state.get('rag_k', 4)
                    similarity_threshold = st.session_state.get('similarity_threshold', 0.2)
                    
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
                                context_parts.append(f"[Fuente: {meta['source']}, Pág: {meta['page']}]\n{doc_text}")
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
                    st.write("") 
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