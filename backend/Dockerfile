FROM python:3.9-slim

# Establecer entorno para no crear archivos .pyc y mantener output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Crear directorio de archivos estáticos
RUN mkdir -p /app/static

# Copiar el código del proyecto
COPY . .

# Script de inicio para Railway
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
python manage.py collectstatic --no-input\n\
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT\n'\
> /app/start.sh && chmod +x /app/start.sh

EXPOSE $PORT
CMD ["/app/start.sh"] 