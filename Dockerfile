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

# Crear script para omitir migraciones en el primer despliegue y agregar logs detallados
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== INICIANDO DESPLIEGUE ==="\n\
echo "Fecha y hora: $(date)"\n\
echo "Directorio actual: $(pwd)"\n\
echo "Contenido del directorio:"\n\
ls -la\n\
\n\
echo "=== CONFIGURACIÓN DE ENTORNO ==="\n\
# Exportar variables de entorno si existe .env.railway\n\
if [ -f /.env.railway ]; then\n\
  echo "Cargando variables desde .env.railway"\n\
  export $(grep -v "^#" /.env.railway | xargs)\n\
  echo "Variables cargadas correctamente"\n\
else\n\
  echo "ADVERTENCIA: Archivo .env.railway no encontrado"\n\
fi\n\
\n\
echo "=== VERIFICACIÓN DE ARCHIVOS CRÍTICOS ==="\n\
if [ -f manage.py ]; then\n\
  echo "manage.py encontrado"\n\
else\n\
  echo "ERROR: manage.py no encontrado"\n\
  ls -la\n\
fi\n\
\n\
echo "=== INICIANDO SERVIDOR GUNICORN ==="\n\
echo "Usando puerto: 8000"\n\
# Solo ejecutar gunicorn, sin migraciones ni collectstatic\n\
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --log-level debug --access-logfile - --error-logfile -\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
CMD ["/app/entrypoint.sh"]

# Exponer puerto fijo
EXPOSE 8000