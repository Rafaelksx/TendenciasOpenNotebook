from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    
    # El candado para que no se repitan los correos
    correo = Column(String(150), unique=True, index=True, nullable=False)
    
    # Contraseña encriptada
    contraseña_hash = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Usuario {self.correo}>"