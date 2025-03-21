FROM python:3.9-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    bash \
    sed \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar todos los archivos del proyecto
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r backend/requirements.txt

# Hacer que los scripts sean ejecutables
RUN chmod +x /app/docker-entrypoint.sh
RUN chmod +x /app/backend/health.py

# Exponer puerto
EXPOSE $PORT

# Comando por defecto
CMD ["/bin/sh", "/app/docker-entrypoint.sh"] 