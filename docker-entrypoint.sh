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

# Iniciar servicios en Railway
start_railway_services() {
  echo "Iniciando servicios con docker-compose..."
  
  # Iniciar servicios backend y frontend primero
  docker-compose -f docker-compose.railway.yml up -d backend frontend
  
  # Iniciar gateway después de que backend esté disponible
  echo "Esperando a que el backend esté listo..."
  for i in $(seq 1 30); do
    if curl -s -f http://localhost:8000/api/health/ > /dev/null; then
      echo "Backend está disponible! Iniciando gateway..."
      docker-compose -f docker-compose.railway.yml up -d gateway
      break
    fi
    if [ $i -eq 30 ]; then
      echo "ADVERTENCIA: No se pudo contactar con el backend después de 30 intentos, pero continuando con el despliegue..."
      docker-compose -f docker-compose.railway.yml up -d gateway
    fi
    echo "Esperando a que el backend esté disponible - intento $i/30"
    sleep 2
  done
  
  echo "Todos los servicios están iniciados!"
}

# Iniciar aplicación dependiendo del entorno
if [ "$RAILWAY_ENVIRONMENT" = "true" ]; then
  echo "Iniciando en entorno Railway..."
  
  # Asegurarnos de que Postgres esté disponible
  if wait_for_postgres; then
    # En Railway, primero iniciamos el health check independiente que escucha en el puerto principal
    echo "Iniciando servicio de health check como punto de entrada principal..."
    docker-compose -f docker-compose.railway.yml up -d health
    
    # Verificar que el health check esté funcionando
    echo "Verificando servicio de health check..."
    for i in $(seq 1 10); do
      if curl -s -f http://localhost:$PORT/health > /dev/null; then
        echo "Servicio de health check está funcionando!"
        
        # Iniciar el resto de los servicios en segundo plano
        start_railway_services &
        
        # Seguir los logs del health check (que es el servicio principal)
        docker-compose -f docker-compose.railway.yml logs -f health
        
        exit 0
      fi
      echo "Esperando que el servicio de health check esté disponible - intento $i/10"
      sleep 2
    done
    
    echo "ERROR: El servicio de health check no está respondiendo. Verificando logs..."
    docker-compose -f docker-compose.railway.yml logs health
    
    # Intentar iniciar el resto de los servicios de todos modos
    echo "Iniciando servicios a pesar del error..."
    start_railway_services
    
    # Seguir todos los logs para diagnóstico
    docker-compose -f docker-compose.railway.yml logs -f
  else
    echo "Error: No se pudo conectar a la base de datos"
    exit 1
  fi
else
  echo "Iniciando en entorno de desarrollo..."
  exec docker-compose up
fi 