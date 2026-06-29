import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db_models import Base 

# La URL de conexión que viene del docker-compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opennotebook_user:opennotebook_pass@db:5432/opennotebook")

# Creamos el motor de conexión
engine = create_engine(DATABASE_URL)

# Creamos la fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea las tablas automáticamente si no existen."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Proveedor de sesiones para la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()