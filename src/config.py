import os

# --- VARIABLES DE ENTORNO Y CONFIGURACIÓN ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
DATA_DIR = os.getenv("DATA_DIR", "./data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")

# Crear directorios si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

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

CUSTOM_CSS = """
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
"""
