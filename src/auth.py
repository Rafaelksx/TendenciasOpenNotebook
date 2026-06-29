import bcrypt
from sqlalchemy.orm import Session
from src.db_models import Usuario

def encriptar_contraseña(contraseña_plana: str) -> str:
    """Transforma la contraseña normal en un texto irreconocible."""
    sal = bcrypt.gensalt()
    # bcrypt necesita que los textos estén en bytes (encode), luego lo devolvemos a texto normal (decode)
    contraseña_hash = bcrypt.hashpw(contraseña_plana.encode('utf-8'), sal)
    return contraseña_hash.decode('utf-8')

def verificar_contraseña(contraseña_plana: str, contraseña_hash: str) -> bool:
    """Compara la contraseña que pone el usuario con la encriptada de la base de datos."""
    return bcrypt.checkpw(contraseña_plana.encode('utf-8'), contraseña_hash.encode('utf-8'))

def registrar_usuario(db: Session, nombre: str, correo: str, contraseña: str):
    """Crea un nuevo usuario en la base de datos."""
    # Primero revisamos si el correo ya existe por si acaso
    usuario_existente = db.query(Usuario).filter(Usuario.correo == correo).first()
    if usuario_existente:
        return None # Esto le dirá a la app que el correo ya está en uso
    
    nuevo_usuario = Usuario(
        nombre=nombre,
        correo=correo,
        contraseña_hash=encriptar_contraseña(contraseña)
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

def autenticar_usuario(db: Session, correo: str, contraseña: str):
    """Valida si el correo existe y si la clave es correcta."""
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    
    if not usuario:
        return False # El correo no existe
        
    if not verificar_contraseña(contraseña, usuario.contraseña_hash):
        return False # La contraseña es incorrecta
        
    return usuario # Login exitoso, devolvemos los datos del usuario