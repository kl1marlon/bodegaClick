FROM node:16-alpine as builder

WORKDIR /app

# Copiar solo package.json para instalar dependencias
# Esto permite mejor caché de Docker
COPY package.json ./

# Instalar solo dependencias de producción para reducir el tiempo y tamaño
RUN npm install --only=production --no-audit --no-fund

# Copiar el resto de los archivos del proyecto
COPY public ./public
COPY src ./src
COPY .env* ./
COPY *.js ./

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

EXPOSE 80

# Comando para iniciar nginx
CMD ["nginx", "-g", "daemon off;"] 