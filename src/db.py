import os
import chromadb
import streamlit as st
from src.config import DATA_DIR

@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma"))

def get_vector_collection(collection_name="open_notebook_docs"):
    client = get_chroma_client()
    try:
        return client.get_collection(name=collection_name)
    except Exception:
        return client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
