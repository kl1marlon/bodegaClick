FROM docker:20.10.16-dind

# Instalar dependencias necesarias
RUN apk add --no-cache \
    docker-compose \
    python3 \
    py3-pip \
    netcat-openbsd \
    curl \
    bash \
    sed

WORKDIR /app

# Copiar todos los archivos del proyecto
COPY . .

# Hacer que los scripts sean ejecutables
RUN chmod +x /app/docker-entrypoint.sh
RUN chmod +x /app/backend/health.py

# Comando por defecto, usando sh para ejecutar el script en lugar de ejecutarlo directamente
CMD ["/bin/sh", "/app/docker-entrypoint.sh"] 