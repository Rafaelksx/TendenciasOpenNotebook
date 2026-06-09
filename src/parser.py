from io import BytesIO
import re
from pypdf import PdfReader
from docx import Document
import streamlit as st
from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.models import get_ollama_embedding

def clean_extracted_text(text):
    if not text:
        return ""
    # Normalizar retornos de carro
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Usar un marcador temporal para saltos de párrafo dobles
    text = re.sub(r'\n\s*\n', ' [PARAGRAPH_BREAK] ', text)
    # Reemplazar saltos de línea simples por espacios
    text = text.replace("\n", " ")
    # Restaurar los saltos de párrafo reales
    text = text.replace(" [PARAGRAPH_BREAK] ", "\n\n")
    # Limpiar espacios múltiples consecuentes
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

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
    doc = Document(BytesIO(file_bytes))
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    cleaned_text = clean_extracted_text("\n\n".join(full_text))
    return [{"text": cleaned_text, "page": 1}]

def extract_text_from_pdf(file_bytes):
    pdf_reader = PdfReader(BytesIO(file_bytes))
    pages_content = []
    for i, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text:
            cleaned_text = clean_extracted_text(text)
            pages_content.append({"text": cleaned_text, "page": i + 1})
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

def ingest_document(collection, filename, file_bytes, file_type):
    with st.spinner(f"Procesando e indexando '{filename}'..."):
        if file_type == "application/pdf":
            pages = extract_text_from_pdf(file_bytes)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith(".docx"):
            pages = extract_text_from_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            cleaned_text = clean_extracted_text(text)
            pages = [{"text": cleaned_text, "page": 1}]
            
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
