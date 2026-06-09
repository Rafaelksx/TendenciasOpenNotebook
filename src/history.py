import os
import json
from src.config import HISTORY_DIR

def get_chat_sessions():
    sessions = []
    if os.path.exists(HISTORY_DIR):
        for f in os.listdir(HISTORY_DIR):
            if f.endswith(".json"):
                session_id = f[:-5]
                filepath = os.path.join(HISTORY_DIR, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        display_name = "Conversación vacía"
                        for msg in data:
                            if msg.get("role") == "user":
                                display_name = msg.get("content")[:30]
                                if len(msg.get("content")) > 30:
                                    display_name += "..."
                                break
                        mtime = os.path.getmtime(filepath)
                        sessions.append((session_id, display_name, mtime))
                except Exception:
                    pass
    sessions.sort(key=lambda x: x[2], reverse=True)
    return [(s[0], s[1]) for s in sessions]

def load_chat_session(session_id):
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_chat_session(session_id, messages):
    if not messages:
        return
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import streamlit as st
        st.error(f"Error guardando sesión de chat: {e}")

def delete_chat_session(session_id):
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass
