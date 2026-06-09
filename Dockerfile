# Imagen base oficial de Python slim
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc en disco y habilitar el buffer de salida para logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar o instalar algunas librerías si hiciera falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar los requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .

# Crear el directorio de datos persistente para la base de datos vectorial
RUN mkdir -p /app/data

# Exponer el puerto por defecto de Streamlit
EXPOSE 8501

# Configuración de Streamlit para ejecutarse correctamente en contenedores sin telemetría
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Comando para iniciar la aplicación
CMD ["streamlit", "run", "app.py"]
