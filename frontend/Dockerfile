FROM node:16-alpine as builder

WORKDIR /app

# Copiar solo package.json y package-lock.json para mejor caché
COPY package*.json ./

# Instalar solo dependencias de producción para reducir el tiempo y tamaño
RUN npm ci --only=production --no-audit --no-fund

# Copiar el resto de los archivos del proyecto
COPY . .

# Configurar variables de entorno para build
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Construir la aplicación
RUN npm run build

# Etapa de producción con imagen más ligera
FROM nginx:alpine

# Eliminar archivos default de nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar solo los archivos de build necesarios
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar la configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Configurar variables para un mejor rendimiento
ENV NODE_ENV=production
ENV NGINX_ENTRYPOINT_QUIET_LOGS=1

# Crear archivo para reemplazar variables de entorno en tiempo de ejecución
RUN echo 'window.RUNTIME_ENV = { API_URL: "${API_URL}" };' > /usr/share/nginx/html/runtime-config.js

# Copiar script de entrada personalizado
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# Usar script de entrada personalizado
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]