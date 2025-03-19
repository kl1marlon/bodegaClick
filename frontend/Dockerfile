FROM node:16

WORKDIR /app

# Copiar archivos de configuración
COPY package*.json ./
RUN npm install

# Copiar el resto de los archivos
COPY . .

# Asegurarse de que el directorio public existe
RUN mkdir -p public

EXPOSE 3000

CMD ["npm", "start"] 