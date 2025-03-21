FROM python:3.9-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    bash \
    sed \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar solo los archivos de requisitos primero para aprovechar la caché de Docker
COPY backend/requirements.txt /app/backend/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar el resto de los archivos
COPY . .

# Hacer que los scripts sean ejecutables
RUN chmod +x /app/docker-entrypoint.sh
RUN chmod +x /app/backend/health.py

# Exponer puerto
EXPOSE ${PORT:-8000}

# Comando por defecto
CMD ["/bin/sh", "/app/docker-entrypoint.sh"] 