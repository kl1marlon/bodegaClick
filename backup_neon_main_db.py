import os
import subprocess
import datetime
import getpass

# --- CONFIGURACIÓN: DETALLES DE TU BASE DE DATOS *PRINCIPAL* ---
# !!! Reemplaza con los valores correctos de tu rama PRINCIPAL de Neon !!!
DB_HOST = 'ep-floral-surf-a4m7e3ws-pooler.us-east-1.aws.neon.tech' # Endpoint de tu rama PRINCIPAL
DB_PORT = "5432"
DB_NAME = "bodegaclicktest"
DB_USER = "bodegaclicktest_owner"
# La contraseña se pedirá de forma segura o se leerá de PGPASSWORD
# --------------------------------------------------------------

# --- Nombre del archivo de backup ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILENAME = f"backup_{DB_NAME}_main_{timestamp}.dump"
# Usamos el formato '.dump' que es el formato custom de pg_dump (comprimido y flexible)

# --- Función principal de backup ---
def create_backup():
    print(f"--- Iniciando backup de la base de datos '{DB_NAME}' (Host: {DB_HOST}) ---")

    # Manejo seguro de la contraseña
    db_password = os.environ.get('PGPASSWORD')
    if not db_password:
        print("Variable de entorno PGPASSWORD no encontrada.")
        try:
            db_password = getpass.getpass(f"Ingrese la contraseña para el usuario '{DB_USER}': ")
        except Exception as e:
            print(f"\nError al leer la contraseña: {e}")
            return False
    else:
        print("Usando contraseña desde la variable de entorno PGPASSWORD.")

    # Crear el entorno para el subproceso, incluyendo PGPASSWORD
    # Esto evita poner la contraseña directamente en el comando
    process_env = os.environ.copy()
    process_env['PGPASSWORD'] = db_password

    # Comando pg_dump
    # -Fc: formato custom (recomendado, comprimido)
    # -Z 0: Sin compresión adicional (el formato custom ya comprime algo) - opcional
    # --blobs: incluir objetos grandes (recomendado)
    command = [
        'pg_dump',
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        '-d', DB_NAME,
        '-Fc',        # Formato Custom
        '--blobs',    # Incluir Large Objects
        '-f', BACKUP_FILENAME
    ]

    print(f"\nEjecutando comando: {' '.join(command[:-1])} -f {BACKUP_FILENAME}")
    print("(La contraseña no se muestra en el comando)")

    try:
        # Ejecutar pg_dump
        # capture_output=True puede consumir mucha memoria para logs grandes,
        # pero es útil para ver errores. text=True decodifica salida/error.
        process = subprocess.run(
            command,
            check=False, # No lanzar excepción en error, lo manejaremos nosotros
            capture_output=True,
            text=True,
            env=process_env # Pasar el entorno con PGPASSWORD
        )

        # Verificar resultado
        if process.returncode == 0:
            print(f"\n--- Backup completado exitosamente ---")
            print(f"Archivo de backup guardado como: {os.path.abspath(BACKUP_FILENAME)}")
            # Opcional: Mostrar tamaño del archivo
            try:
                size_bytes = os.path.getsize(BACKUP_FILENAME)
                print(f"Tamaño del archivo: {size_bytes / (1024*1024):.2f} MB")
            except OSError:
                pass # Ignorar si no se puede obtener tamaño
            return True
        else:
            print(f"\n--- ERROR durante el backup ---")
            print(f"pg_dump devolvió el código de error: {process.returncode}")
            print("\nSalida de error de pg_dump:")
            print("-" * 30)
            print(process.stderr if process.stderr else "(Sin salida de error estándar)")
            print("-" * 30)
            # Intentar borrar archivo parcial si falló
            if os.path.exists(BACKUP_FILENAME):
                try:
                    os.remove(BACKUP_FILENAME)
                    print(f"Archivo de backup parcial '{BACKUP_FILENAME}' eliminado.")
                except OSError as e:
                    print(f"No se pudo eliminar el archivo parcial '{BACKUP_FILENAME}': {e}")
            return False

    except FileNotFoundError:
        print("\n--- ERROR ---")
        print("Comando 'pg_dump' no encontrado.")
        print("Asegúrate de que las herramientas de cliente de PostgreSQL estén instaladas y en el PATH del sistema.")
        return False
    except Exception as e:
        print(f"\n--- ERROR INESPERADO ---")
        print(f"Ocurrió un error durante la ejecución: {e}")
        return False

# --- Punto de entrada ---
if __name__ == "__main__":
    # Doble verificación antes de empezar
    print("*" * 60)
    print("ADVERTENCIA: Este script creará un backup de la BD especificada.")
    print(f"Host:   {DB_HOST}")
    print(f"Puerto: {DB_PORT}")
    print(f"BD:     {DB_NAME}")
    print(f"Usuario:{DB_USER}")
    print("Por favor, VERIFICA que estos son los detalles de la base de datos PRINCIPAL que deseas respaldar.")
    print("*" * 60)

    confirm = input("¿Deseas continuar? (s/N): ").lower()
    if confirm == 's':
        create_backup()
    else:
        print("Backup cancelado por el usuario.")