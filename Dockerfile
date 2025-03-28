FROM python:3.9-slim

# Establecer entorno para no crear archivos .pyc y mantener output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de entorno si existen
COPY backend/requirements.txt .
COPY .env.railway /.env.railway

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary dj-database-url \
    && rm -rf ~/.cache/pip

# Copiar el código del proyecto
COPY backend/ .

# Comando para ejecución en producción
CMD ["sh", "-c", "if [ -f /.env.railway ]; then export $(grep -v '^#' /.env.railway | xargs); fi && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]

# El puerto será definido por Railway mediante la variable PORT
EXPOSE ${PORT:-8000} 