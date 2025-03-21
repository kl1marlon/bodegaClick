#!/bin/sh
set -e

# Configurar variables de entorno para Railway
if [ -n "$PORT" ]; then
  echo "Puerto asignado por Railway: $PORT"
  echo "Detectado entorno Railway"
  export RAILWAY_ENVIRONMENT=true
  
  # Priorizar DATABASE_PUBLIC_URL sobre DATABASE_URL
  if [ -n "$DATABASE_PUBLIC_URL" ]; then
    echo "Usando DATABASE_PUBLIC_URL para conexiones externas"
    # Convertir postgres:// a postgresql:// si es necesario
    if echo "$DATABASE_PUBLIC_URL" | grep -q "^postgres://"; then
      DATABASE_PUBLIC_URL=$(echo "$DATABASE_PUBLIC_URL" | sed 's/^postgres:\/\//postgresql:\/\//')
      echo "URL convertida a formato postgresql://"
    fi
    export DATABASE_URL="$DATABASE_PUBLIC_URL"
  else
    echo "DATABASE_PUBLIC_URL no encontrada, usando DATABASE_URL"
  fi
  
  # Mostrar información relevante para debug
  echo "Información de conexión a la base de datos:"
  echo "DATABASE_URL: $DATABASE_URL"
  echo "PGHOST: $PGHOST"
  echo "PGPORT: $PGPORT"
  echo "PGUSER: $PGUSER"
  echo "PGDATABASE: $PGDATABASE"
  
  # Crear un archivo .env para la aplicación
  echo "PORT=$PORT" > .env
  echo "DATABASE_URL=$DATABASE_URL" >> .env
  if [ -n "$DATABASE_PUBLIC_URL" ]; then
    echo "DATABASE_PUBLIC_URL=$DATABASE_PUBLIC_URL" >> .env
  fi
  echo "LOYVERSE_API_TOKEN=$LOYVERSE_API_TOKEN" >> .env
  echo "RAILWAY_STATIC_URL=$RAILWAY_STATIC_URL" >> .env
  echo "RAILWAY_ENVIRONMENT=true" >> .env
fi

# Función para esperar a que Postgres esté disponible
wait_for_postgres() {
  echo "Esperando que PostgreSQL esté disponible..."
  
  # Priorizar PGHOST y PGPORT si están disponibles
  if [ -n "$PGHOST" ] && [ -n "$PGPORT" ]; then
    DB_HOST=$PGHOST
    DB_PORT=$PGPORT
    echo "Usando variables PGHOST=$DB_HOST y PGPORT=$DB_PORT para conexión"
  elif [ -n "$DATABASE_URL" ]; then
    # Extraer host y puerto de DATABASE_URL si PGHOST no está disponible
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if [ -z "$DB_PORT" ]; then
      DB_PORT=5432
    fi
    echo "Extrayendo host=$DB_HOST y puerto=$DB_PORT de DATABASE_URL"
  else
    echo "No se encontraron variables de conexión a la base de datos"
    return 1
  fi
  
  echo "Verificando conexión a base de datos en $DB_HOST:$DB_PORT"
  
  # Intentar conectarse directamente a postgres
  for i in $(seq 1 30); do
    if nc -z $DB_HOST $DB_PORT; then
      echo "PostgreSQL está disponible!"
      return 0
    fi
    echo "PostgreSQL no está disponible todavía - intento $i/30"
    sleep 2
  done
  
  echo "ERROR: No se pudo conectar a PostgreSQL después de 30 intentos"
  # Continuar de todos modos si no podemos verificar la conexión a postgres
  echo "Intentando continuar de todos modos..."
  return 0
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
  wait_for_postgres
  
  # Iniciar la aplicación sin Docker
  start_railway_app
else
  echo "Iniciando en entorno de desarrollo..."
  if command -v docker-compose >/dev/null 2>&1; then
    exec docker-compose up
  else
    echo "Docker Compose no está disponible. Ejecutando en modo alternativo..."
    start_railway_app
  fi
fi 