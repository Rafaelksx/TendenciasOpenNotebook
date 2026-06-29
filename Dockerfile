FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos absolutamente todo el directorio a /app
COPY . .

# Creamos el directorio de datos
RUN mkdir -p /app/data

# No ponemos CMD aquí, lo controlaremos desde el docker-compose