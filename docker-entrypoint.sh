#!/bin/sh
set -e

# Configurar variables de entorno para Railway
if [ -n "$PORT" ]; then
  echo "Puerto asignado por Railway: $PORT"
  echo "Detectado entorno Railway"
  export RAILWAY_ENVIRONMENT=true
  
  # Crear un archivo .env para la aplicación
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

# Ejecutar aplicación en Railway sin usar Docker
start_railway_app() {
  echo "Iniciando aplicación en Railway directamente (sin Docker)..."
  
  # Ejecutar el script de health check
  echo "Iniciando health check en puerto $PORT..."
  cd /app
  python3 /app/backend/health.py &
  HEALTH_PID=$!
  
  # Iniciar el backend directamente
  echo "Iniciando backend..."
  cd /app/backend
  python3 manage.py migrate
  python3 manage.py collectstatic --noinput
  gunicorn --workers=2 --threads=4 --timeout=120 --bind 0.0.0.0:8000 config.wsgi:application &
  BACKEND_PID=$!
  
  # Mantenemos el proceso principal ejecutándose
  wait $HEALTH_PID
}

# Iniciar aplicación dependiendo del entorno
if [ "$RAILWAY_ENVIRONMENT" = "true" ]; then
  echo "Iniciando en entorno Railway..."
  
  # Asegurarnos de que Postgres esté disponible
  if wait_for_postgres; then
    # Iniciar la aplicación sin Docker
    start_railway_app
  else
    echo "Error: No se pudo conectar a la base de datos"
    exit 1
  fi
else
  echo "Iniciando en entorno de desarrollo..."
  if command -v docker-compose >/dev/null 2>&1; then
    exec docker-compose up
  else
    echo "Docker Compose no está disponible. Ejecutando en modo alternativo..."
    start_railway_app
  fi
fi 