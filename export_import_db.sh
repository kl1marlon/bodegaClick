#!/bin/bash

# Script para exportar e importar la base de datos de BodegaClick a Railway

# Función para exportar la base de datos
export_database() {
  echo "Exportando base de datos local..."
  
  # Obtener ID del contenedor de PostgreSQL
  CONTAINER_ID=$(docker ps -qf "name=postgres")
  
  if [ -z "$CONTAINER_ID" ]; then
    echo "Error: No se encontró el contenedor de PostgreSQL. Asegúrate de que Docker esté en ejecución."
    exit 1
  fi
  
  # Exportar base de datos
  echo "Exportando desde el contenedor $CONTAINER_ID..."
  docker exec -t $CONTAINER_ID pg_dump -U postgres facturacion_db > backup_bodegaclick.sql
  
  if [ $? -eq 0 ]; then
    echo "Base de datos exportada con éxito a backup_bodegaclick.sql"
  else
    echo "Error al exportar la base de datos."
    exit 1
  fi
}

# Función para importar la base de datos a Railway
import_database() {
  echo "Importando base de datos a Railway..."
  
  # Verificar si Railway CLI está instalado
  if ! command -v railway &> /dev/null; then
    echo "Railway CLI no está instalado. Instalando..."
    npm i -g @railway/cli
  fi
  
  # Autenticar en Railway si es necesario
  railway status &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Por favor, autentícate en Railway..."
    railway login
  fi
  
  # Vincular al proyecto
  echo "Conectando al proyecto Railway..."
  railway link
  
  # Conectar a la base de datos PostgreSQL
  echo "Conectando a la base de datos PostgreSQL en Railway..."
  echo "Nota: Una vez conectado, ejecuta el siguiente comando para importar:"
  echo "\i ruta/completa/a/backup_bodegaclick.sql"
  echo "Luego puedes salir con \q"
  
  railway connect postgresql
}

# Función principal
main() {
  case "$1" in
    export)
      export_database
      ;;
    import)
      import_database
      ;;
    *)
      echo "Uso: $0 {export|import}"
      echo "  export - Exporta la base de datos local a un archivo SQL"
      echo "  import - Conecta a Railway para importar el archivo SQL"
      exit 1
      ;;
  esac
}

# Ejecutar función principal
main "$@" 