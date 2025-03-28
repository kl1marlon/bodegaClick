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

# Crear script para manejar migraciones con reintentos
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Exportar variables de entorno si existe .env.railway\n\
if [ -f /.env.railway ]; then\n\
  export $(grep -v "^#" /.env.railway | xargs)\n\
fi\n\
\n\
# Intentar migraciones normalmente\n\
python manage.py migrate || {\n\
  echo "Migración fallida, intentando con --fake..."\n\
  # Si la migración falla, intentar aplicarla como fake\n\
  python manage.py showmigrations | grep -v "[X]" | grep -oP "(?<=\[ \]) \K.*" | while read -r migration; do\n\
    echo "Intentando migración fake para: $migration"\n\
    python manage.py migrate ${migration%% *} ${migration#* } --fake || true\n\
  done\n\
  # Intentar nuevamente las migraciones normales después de fake\n\
  python manage.py migrate || echo "No se pudieron completar todas las migraciones"\n\
}\n\
\n\
# Continuar con el resto de comandos\n\
python manage.py collectstatic --noinput\n\
exec gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
CMD ["/app/entrypoint.sh"]

# El puerto será definido por Railway mediante la variable PORT
EXPOSE ${PORT:-8000} 