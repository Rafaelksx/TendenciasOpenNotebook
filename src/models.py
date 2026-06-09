import requests
import numpy as np
import streamlit as st
from src.config import OLLAMA_BASE_URL, EMBEDDING_MODEL

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
