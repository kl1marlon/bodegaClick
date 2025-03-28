FROM node:16 as builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar el resto de los archivos del proyecto
COPY . .

# Construir la aplicación
RUN npm run build

# Etapa de producción
FROM nginx:stable

# Eliminar archivos default de nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar los archivos de build
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar la configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Configurar variables para un mejor rendimiento
ENV NODE_ENV=production

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]