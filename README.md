# 📖 Open Notebook - Plataforma RAG Local

Este proyecto implementa una libreta inteligente y copiloto de estudio basada en una arquitectura **RAG (Retrieval-Augmented Generation)** que se ejecuta de forma **100% local y desconectada de la red**, garantizando la privacidad absoluta de tus documentos académicos e investigaciones.

## 🛠️ Requisitos Previos

- **Docker Desktop** (con soporte para WSL2 activado en Windows)
- **Nvidia GPU Users**: Tener instalado [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) para habilitar la aceleración por GPU dentro de Docker.
- **AMD GPU Users**: Descargar e instalar [Ollama para Windows](https://ollama.com/download/windows) nativamente en el host.

---

## 🚀 Opción A: Despliegue con Aceleración NVIDIA / CPU (Docker Completo)

Este método levanta tanto la interfaz de usuario como el motor de inferencia (Ollama) dentro de contenedores Docker.

### Paso 1: Iniciar los contenedores
Abre una terminal en la carpeta raíz del proyecto y ejecuta:
```bash
docker compose up -d --build
```

### Paso 2: Aprovisionar los Modelos en Ollama
Dado que Ollama se inicia vacío, debes indicarle que descargue el LLM y el modelo de embeddings ejecutando:
```bash
# Descarga del LLM Qwen 2.5 1.5B (Cuantizado a Q4_K_M)
docker exec -it open_notebook_ollama ollama pull qwen2.5:1.5b

# Descarga del Codificador Semántico Nomic Embed v1.5
docker exec -it open_notebook_ollama ollama pull nomic-embed-text
```

### Paso 3: Acceder a la aplicación
Una vez descargados los modelos, abre tu navegador e ingresa a:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🚀 Opción B: Despliegue con Aceleración AMD (Ollama Nativo + Docker App)

Debido a que Docker Desktop en Windows no soporta el acceso directo a GPUs AMD, utilizamos Ollama corriendo directamente en Windows (el cual tiene soporte de fábrica para AMD Radeon/ROCm) y conectamos la app de Docker a este servicio.

### Paso 1: Configurar y Ejecutar Ollama en Windows
1. Descarga e instala **Ollama para Windows**.
2. Abre la terminal de Windows (PowerShell o CMD) y descarga los modelos localmente:
   ```powershell
   ollama pull qwen2.5:1.5b
   ollama pull nomic-embed-text
   ```
3. Asegúrate de que Ollama se esté ejecutando en segundo plano en la barra de tareas de Windows.

### Paso 2: Levantar el Frontend de Open Notebook en Docker
Utiliza el archivo de orquestación alternativo `docker-compose-amd.yml` que apunta directamente al host físico de Windows:
```bash
docker compose -f docker-compose-amd.yml up -d --build
```

### Paso 3: Acceder a la aplicación
Abre tu navegador e ingresa a:
👉 **[http://localhost:8501](http://localhost:8501)**

*(La aplicación detectará de forma automática el servidor de Ollama del host y confirmará la presencia de los modelos descargados en el paso 1).*

---

## 🧠 Detalles Técnicos Clave

1. **Matryoshka Embeddings (Truncado a 256d y Normalización L2)**:
   El modelo `nomic-embed-text` genera vectores de 768 dimensiones por defecto. Para optimizar drásticamente la búsqueda vectorial en entornos con recursos de CPU limitados, la aplicación aplica la reducción Matryoshka truncando el vector a **256 dimensiones** y re-normalizando mediante la norma L2. Esto disminuye un 66% el consumo de memoria y almacenamiento con una pérdida de precisión inferior al 1%.
   
2. **Prefijos obligatorios de Nomic**:
   - Al indexar los textos (ingesta), se añade automáticamente el prefijo `search_document: ` a cada fragmento.
   - Al realizar una consulta, se añade el prefijo `search_query: ` a la pregunta antes de vectorizarla.
   
3. **Persistencia**:
   - Los archivos indexados y la base de datos vectorial se guardan en el volumen de Docker `vdb_storage` (mapeado a `/app/data` dentro del contenedor), garantizando que no se pierdan al apagar los contenedores.
   - Los pesos de los modelos de Ollama de la Opción A se guardan en el volumen persistente `ollama_storage`.
