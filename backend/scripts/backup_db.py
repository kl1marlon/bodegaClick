import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(DOTENV_PATH)

# Obtener variables de entorno
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    raise Exception("Faltan variables de entorno requeridas: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")

# Crear nombre de archivo de backup con timestamp
fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = f"backup_{DB_NAME}_{fecha}.sql"
backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), backup_filename)

# Comando para realizar el backup
command = [
    'pg_dump',
    '-h', DB_HOST,
    '-p', DB_PORT,
    '-U', DB_USER,
    '-F', 'p',  # Formato plano SQL compatible con cualquier version
    '-b',       # Incluir blobs
    '-v',       # Verbose
    '-f', backup_path,
    DB_NAME
]

# Establecer la variable de entorno PGPASSWORD temporalmente
env = os.environ.copy()
env['PGPASSWORD'] = DB_PASSWORD

print(f"Realizando backup de la base de datos '{DB_NAME}' en '{backup_path}'...")
try:
    subprocess.run(command, env=env, check=True)
    print("Backup completado con éxito.")
except subprocess.CalledProcessError as e:
    print(f"Error realizando el backup: {e}")
