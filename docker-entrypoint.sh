#!/bin/sh
set -e

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
    for i in $(seq 1 30); do
      if nc -z $DB_HOST $DB_PORT; then
        echo "PostgreSQL está disponible!"
        return 0
      fi
      echo "PostgreSQL no está disponible todavía - intento $i/30"
      sleep 2
    done
    
    echo "ERROR: No se pudo conectar a PostgreSQL después de 30 intentos"
    return 1
  else
    echo "DATABASE_URL no está definido, saltando verificación de PostgreSQL"
    return 0
  fi
}

# Iniciar aplicación dependiendo del entorno
if [ "$RAILWAY_ENVIRONMENT" = "true" ]; then
  echo "Iniciando en entorno Railway..."
  
  # Primero iniciar el servicio de health check independiente
  echo "Iniciando servicio de health check independiente..."
  docker-compose -f docker-compose.railway.yml up -d health
  
  # Verificar si el servicio de health check está funcionando
  echo "Verificando servicio de health check..."
  for i in $(seq 1 10); do
    if curl -s -f http://localhost:8001/health > /dev/null; then
      echo "Servicio de health check está funcionando!"
      break
    fi
    echo "Esperando que el servicio de health check esté disponible - intento $i/10"
    sleep 2
  done
  
  # Continuar con el resto de los servicios
  if wait_for_postgres; then
    echo "Iniciando servicios con docker-compose..."
    # Iniciar servicios
    docker-compose -f docker-compose.railway.yml up -d backend frontend gateway
    
    # Seguir los logs de todos los contenedores
    docker-compose -f docker-compose.railway.yml logs -f
  else
    echo "Error: No se pudo conectar a la base de datos"
    exit 1
  fi
else
  echo "Iniciando en entorno de desarrollo..."
  exec docker-compose up
fi 