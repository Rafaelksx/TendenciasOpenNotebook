from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.db import get_chroma_client

# Importamos las funciones que ya creaste en la carpeta src
from src.auth_db import get_db, init_db
from src.auth import registrar_usuario, autenticar_usuario

# Inicializamos la API
app = FastAPI(title="Open Notebook API Backend")

# --- CONFIGURACIÓN CORS (CRÍTICO PARA QUE STREAMLIT PUEDA CONECTARSE) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se pone la IP del frontend, localmente "*" está bien
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- EVENTO DE INICIO ---
@app.on_event("startup")
def startup_event():
    """Crea las tablas en PostgreSQL apenas arranca el servidor FastAPI"""
    init_db()

# --- ESQUEMAS DE VALIDACIÓN (PYDANTIC) ---
class UsuarioRegistro(BaseModel):
    nombre: str
    correo: str
    contraseña: str

class UsuarioLogin(BaseModel):
    correo: str
    contraseña: str

# --- RUTAS / ENDPOINTS ---

@app.post("/registro")
def registro(user: UsuarioRegistro, db: Session = Depends(get_db)):
    """Ruta para crear un nuevo usuario"""
    nuevo_usuario = registrar_usuario(db, user.nombre, user.correo, user.contraseña)
    
    if not nuevo_usuario:
        # El código 400 le dirá a Streamlit que muestre un mensaje de error rojo
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
    return {"mensaje": "Usuario creado exitosamente", "correo": nuevo_usuario.correo}

@app.post("/login")
def login(user: UsuarioLogin, db: Session = Depends(get_db)):
    """Ruta para verificar credenciales e iniciar sesión"""
    usuario_valido = autenticar_usuario(db, user.correo, user.contraseña)
    
    if not usuario_valido:
        # El código 401 significa "No Autorizado"
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Si todo sale bien, devolvemos los datos para que Streamlit los guarde en su session_state
    return {
        "mensaje": "Login exitoso", 
        "usuario": {
            "id": usuario_valido.id,
            "nombre": usuario_valido.nombre,
            "correo": usuario_valido.correo
        }
    }