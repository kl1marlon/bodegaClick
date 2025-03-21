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
RUN chmod +x /app/backend/health.py

# Exponer puerto
EXPOSE 8000

# Comando simple para iniciar la aplicación directamente
CMD cd /app/backend && \
    python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn --workers=2 --threads=4 --timeout=120 --bind 0.0.0.0:$PORT config.wsgi:application 