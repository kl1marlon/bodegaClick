#!/bin/sh
set -e

# Función para esperar a que Postgres esté disponible
wait_for_postgres() {
  echo "Esperando que PostgreSQL esté disponible..."
  # Extraer las variables de conexión de DATABASE_URL
  if [ -n "$DATABASE_URL" ]; then
    # Usamos sed para extraer host y puerto
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if [ -z "$DB_PORT" ]; then
      DB_PORT=5432
    fi
    
    echo "Verificando conexión a base de datos en $DB_HOST:$DB_PORT"
    
    # Esperar a que el puerto esté disponible
    until nc -z $DB_HOST $DB_PORT; do
      echo "PostgreSQL no está disponible todavía - esperando..."
      sleep 1
    done
    
    echo "PostgreSQL está disponible!"
  else
    echo "DATABASE_URL no está definido, saltando verificación de PostgreSQL"
  fi
}

# Configurar variables de entorno para Railway
if [ -n "$PORT" ]; then
  echo "Puerto asignado por Railway: $PORT"
  
  # Crear un archivo .env para que Docker Compose pueda usarlo
  echo "PORT=$PORT" > .env
  echo "DATABASE_URL=$DATABASE_URL" >> .env
  echo "LOYVERSE_API_TOKEN=$LOYVERSE_API_TOKEN" >> .env
  echo "RAILWAY_STATIC_URL=$RAILWAY_STATIC_URL" >> .env
  echo "RAILWAY_ENVIRONMENT=true" >> .env
fi

# Iniciar aplicación dependiendo del entorno
if [ "$RAILWAY_ENVIRONMENT" = "true" ]; then
  echo "Iniciando en entorno Railway..."
  wait_for_postgres
  exec docker-compose -f docker-compose.railway.yml up
else
  echo "Iniciando en entorno de desarrollo..."
  exec docker-compose up
fi 