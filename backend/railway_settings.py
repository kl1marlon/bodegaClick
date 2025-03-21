import os
import re

# Priorizar DATABASE_PUBLIC_URL sobre DATABASE_URL si está disponible
if 'RAILWAY_ENVIRONMENT' in os.environ:
    if 'DATABASE_PUBLIC_URL' in os.environ:
        # Usar DATABASE_PUBLIC_URL para conexiones externas
        database_url = os.environ.get('DATABASE_PUBLIC_URL')
        print(f"Usando DATABASE_PUBLIC_URL para conexión externa: {database_url}")
    elif 'DATABASE_URL' in os.environ:
        # Usar DATABASE_URL como respaldo
        database_url = os.environ.get('DATABASE_URL')
        print(f"Usando DATABASE_URL como respaldo: {database_url}")
    else:
        print("ADVERTENCIA: No se encontró ninguna URL de base de datos")
        database_url = None
    
    # Si tenemos una URL de base de datos, asegurarnos que tenga el formato correcto
    if database_url:
        # Si es una URL postgres://, convertirla a postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Establecer DATABASE_URL como la URL modificada
        os.environ['DATABASE_URL'] = database_url
        print(f"URL de base de datos configurada: {database_url}")

# Establecer ALLOWED_HOSTS para Railway
if 'RAILWAY_STATIC_URL' in os.environ:
    railway_domain = re.sub(r'^https?://', '', os.environ.get('RAILWAY_STATIC_URL'))
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
    if railway_domain and railway_domain not in allowed_hosts:
        os.environ['ALLOWED_HOSTS'] = f"{allowed_hosts},{railway_domain}" if allowed_hosts else railway_domain