FROM nginx:alpine

# Configurar variables para Railway
ENV PORT=80
EXPOSE 80

# Crear un directorio para archivos estáticos mínimos
RUN mkdir -p /usr/share/nginx/html

# Crear un archivo HTML estático mínimo para recuperación
RUN echo '<!DOCTYPE html><html><head><title>BodegaClick - Recuperación</title></head><body><h1>Servidor de recuperación de BodegaClick</h1><p>Esta es una versión mínima para recuperar el despliegue en Coolify.</p></body></html>' > /usr/share/nginx/html/index.html

# Crear un archivo de configuración simple para nginx
RUN echo 'server { listen $PORT; location / { root /usr/share/nginx/html; index index.html; } }' > /etc/nginx/conf.d/default.conf

# Crear un script de entrada simple
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf' >> /entrypoint.sh && \
    echo 'echo "Servidor de recuperación iniciado en puerto $PORT"' >> /entrypoint.sh && \
    echo 'nginx -g "daemon off;"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Usar el script directamente
CMD ["/entrypoint.sh"] 