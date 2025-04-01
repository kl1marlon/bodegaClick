FROM node:16-alpine as build

WORKDIR /app

# Recibir variable de entorno durante la construcción
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Copiar solo package.json para instalar dependencias
# Esto permite mejor caché de Docker
COPY package.json package-lock.json ./

# Instalar todas las dependencias necesarias para la construcción
RUN npm ci

# Copiar el resto de los archivos del proyecto
COPY . .

# Mostrar el valor de la variable para depuración
RUN echo "Construyendo con REACT_APP_API_URL=$REACT_APP_API_URL"

# Construir la aplicación (CI=false para ignorar warnings)
ENV CI=false
RUN npm run build || (cat /app/npm-debug.log && exit 1)

# Etapa de producción con imagen más ligera
FROM nginx:1.21-alpine

# Eliminar archivos default de nginx
RUN rm -rf /usr/share/nginx/html/* && rm /etc/nginx/conf.d/default.conf

# Copiar solo los archivos de build necesarios
COPY --from=build /app/build /usr/share/nginx/html

# Copiar la configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Configurar variables para Railway
ENV PORT=80
EXPOSE 80

# Crear un script de entrada que genere un archivo de configuración dinámico
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'sed -i "s/RAILWAY_PORT/$PORT/g" /etc/nginx/conf.d/nginx.conf' >> /entrypoint.sh && \
    echo 'sed -i "s|RAILWAY_BACKEND_URL|$BACKEND_URL|g" /etc/nginx/conf.d/nginx.conf' >> /entrypoint.sh && \
    echo 'echo "window.ENV = { API_URL: \"$BACKEND_URL/api\" };" > /usr/share/nginx/html/config.js' >> /entrypoint.sh && \
    echo 'echo "Configuración generada con BACKEND_URL=$BACKEND_URL"' >> /entrypoint.sh && \
    echo 'nginx -g "daemon off;"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Usar el script directamente
CMD ["/entrypoint.sh"] 