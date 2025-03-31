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
# Borrar migración problemática si existe\n\
if [ -f facturacion/migrations/0013_producto_aplicar_iva.py ]; then\n\
  rm facturacion/migrations/0013_producto_aplicar_iva.py\n\
fi\n\
# Forzar que todas las migraciones se marquen como aplicadas\n\
python manage.py migrate --fake facturacion\n\
# Luego realizar migraciones normales para otras apps\n\
python manage.py migrate\n\
python manage.py collectstatic --no-input\n\
# Iniciar el servidor Django o el worker Celery según la variable de entorno\n\
if [ "$PROCESS_TYPE" = "worker" ]; then\n\
  celery -A config worker --loglevel=info\n\
else\n\
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT\n\
fi\n'\
> /app/start.sh && chmod +x /app/start.sh

EXPOSE $PORT
CMD ["/app/start.sh"] 