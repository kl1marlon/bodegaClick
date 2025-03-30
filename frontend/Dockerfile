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
RUN rm -rf /usr/share/nginx/html/* && rm /etc/nginx/conf.d/default.conf

# Copiar solo los archivos de build necesarios
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar la configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/

# Configurar variables para Railway
ENV PORT=80
EXPOSE 80

# Eliminar el script de entrada personalizado y usar bash directamente
CMD ["/bin/sh", "-c", "sed -i \"s|listen 80|listen $PORT|g\" /etc/nginx/conf.d/nginx.conf && sed -i \"s|\\${BACKEND_URL}|$BACKEND_URL|g\" /etc/nginx/conf.d/nginx.conf && nginx -g \"daemon off;\""] 