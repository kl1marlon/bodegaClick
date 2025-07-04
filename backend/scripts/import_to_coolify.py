import os
import sys
import subprocess
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(DOTENV_PATH)

# Obtener variables de entorno para Coolify
DB_HOST = os.getenv('COOLIFY_POSTGRES_HOST')
DB_PORT = os.getenv('COOLIFY_POSTGRES_PORT', '5432')
DB_NAME = os.getenv('COOLIFY_POSTGRES_DB')
DB_USER = os.getenv('COOLIFY_POSTGRES_USER')
DB_PASSWORD = os.getenv('COOLIFY_POSTGRES_PASSWORD')

# Verificar que todas las variables estén definidas
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    print("Error: Faltan variables de entorno para la conexión a Coolify.")
    print(f"HOST: {DB_HOST}, PORT: {DB_PORT}, DB: {DB_NAME}, USER: {DB_USER}")
    print("PASSWORD: " + ("*" * len(DB_PASSWORD) if DB_PASSWORD else "No definida"))
    sys.exit(1)

# Usar directamente el archivo backup_bodegaclick_prueba.sql
script_dir = os.path.dirname(os.path.abspath(__file__))
backup_file = "backup_bodegaclick_prueba.sql"
backup_path = os.path.join(script_dir, backup_file)

if not os.path.exists(backup_path):
    print(f"Error: No se encontró el archivo {backup_file} en el directorio.")
    print(f"Ruta buscada: {backup_path}")
    print("Archivos disponibles:")
    for file in os.listdir(script_dir):
        if file.endswith(".sql"):
            print(f"- {file}")
    sys.exit(1)

print(f"Se utilizará el archivo: {backup_file}")
print(f"Ruta completa: {backup_path}")

# Comando para restaurar el backup
command = [
    'psql',
    '-h', DB_HOST,
    '-p', DB_PORT,
    '-U', DB_USER,
    '-d', DB_NAME,
    '-f', backup_path
]

# Establecer la variable de entorno PGPASSWORD temporalmente
env = os.environ.copy()
env['PGPASSWORD'] = DB_PASSWORD

print(f"\nImportando backup a la base de datos '{DB_NAME}' en Coolify...")
print(f"Host: {DB_HOST}, Puerto: {DB_PORT}, Usuario: {DB_USER}")

try:
    # Ejecutar el comando
    result = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
    
    # Mostrar salida
    if result.stdout:
        print("\nSalida del comando:")
        print(result.stdout)
    
    if result.stderr:
        print("\nAdvertencias/Errores:")
        print(result.stderr)
    
    print("\nImportación completada con éxito.")
    
except subprocess.CalledProcessError as e:
    print(f"\nError durante la importación: {e}")
    if e.stdout:
        print("\nSalida del comando:")
        print(e.stdout)
    if e.stderr:
        print("\nMensaje de error:")
        print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"\nError inesperado: {e}")
    sys.exit(1)
