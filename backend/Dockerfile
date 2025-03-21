FROM python:3.9-slim

# Establecer entorno para no crear archivos .pyc y mantener output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise dj-database-url \
    && rm -rf ~/.cache/pip

# Copiar el código del proyecto
COPY . .

# Puerto a exponer (Railway sobreescribirá esto con su variable PORT)
EXPOSE 8000

# Verificar salud
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:$PORT/api/health/ || exit 1

# Comando para Railway que ejecuta migraciones y luego inicia el servidor
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn --workers=2 --threads=4 --timeout=120 --bind 0.0.0.0:$PORT config.wsgi:application 