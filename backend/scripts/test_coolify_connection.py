import os
import sys
import psycopg2
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

# Intentar conexión
print(f"Intentando conectar a PostgreSQL en Coolify...")
print(f"Host: {DB_HOST}, Puerto: {DB_PORT}, DB: {DB_NAME}, Usuario: {DB_USER}")

try:
    # Establecer conexión
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    # Crear un cursor
    cursor = conn.cursor()
    
    # Ejecutar consulta simple para verificar conexión
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("\n¡Conexión exitosa!")
    print(f"Versión de PostgreSQL: {db_version[0]}")
    
    # Mostrar tablas existentes
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    if tables:
        print("\nTablas existentes en la base de datos:")
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("\nNo hay tablas en la base de datos.")
    
    # Cerrar cursor y conexión
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\nError al conectar a la base de datos: {e}")
    sys.exit(1)
