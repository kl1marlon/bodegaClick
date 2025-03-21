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

# Comando por defecto, aunque Railway usará el comando en railway.toml
ENTRYPOINT ["/app/docker-entrypoint.sh"] 