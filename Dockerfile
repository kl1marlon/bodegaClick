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
# IMPORTANTE: Notar que copiamos al directorio principal, no dentro de otro directorio
COPY backend/ /app/

# Crear directorio que asegure que el módulo backend sea importable
RUN mkdir -p /app/backend && \
    touch /app/backend/__init__.py

# Crear script para iniciar la aplicación con logging detallado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== INICIANDO DESPLIEGUE ==="\n\
echo "Fecha y hora: $(date)"\n\
echo "Directorio actual: $(pwd)"\n\
echo "Contenido del directorio:"\n\
ls -la\n\
\n\
echo "=== ESTRUCTURA DEL PROYECTO ==="\n\
echo "Verificando estructura del proyecto..."\n\
find . -type f -name "*.py" | sort\n\
\n\
echo "=== VERIFICANDO CONFIGURACIÓN DEL WSGI ==="\n\
if [ -f wsgi.py ]; then\n\
  echo "wsgi.py encontrado en la raíz"\n\
  WSGI_APP="wsgi:application"\n\
elif [ -f backend/wsgi.py ]; then\n\
  echo "backend/wsgi.py encontrado"\n\
  WSGI_APP="backend.wsgi:application"\n\
else\n\
  echo "ERROR: No se encontró el archivo wsgi.py"\n\
  ls -la\n\
  exit 1\n\
fi\n\
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
# Configuración del puerto\n\
if [ -z "${PORT}" ]; then\n\
  echo "Variable de entorno PORT no establecida, usando puerto predeterminado 8000"\n\
  export PORT=8000\n\
else\n\
  echo "Usando puerto definido por Railway: ${PORT}"\n\
fi\n\
\n\
# Verificar entorno Python\n\
echo "=== PYTHON PATH ==="\n\
echo $PYTHONPATH\n\
echo "=== PYTHON MODULES ==="\n\
pip list\n\
\n\
echo "=== INICIANDO SERVIDOR GUNICORN ==="\n\
echo "Usando puerto: ${PORT}"\n\
echo "Usando WSGI app: ${WSGI_APP}"\n\
# Ejecutar gunicorn con configuración detallada de logs\n\
exec gunicorn ${WSGI_APP} \\\n\
  --bind 0.0.0.0:${PORT} \\\n\
  --workers 2 \\\n\
  --threads 2 \\\n\
  --timeout 30 \\\n\
  --graceful-timeout 30 \\\n\
  --keep-alive 5 \\\n\
  --log-level debug \\\n\
  --access-logfile - \\\n\
  --error-logfile -\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
CMD ["/app/entrypoint.sh"]

# Puerto será asignado por Railway
ENV PORT=8000
# Usar el valor de la variable de entorno PORT
EXPOSE 8000