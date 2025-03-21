import os
import re

# Si estamos en Railway y se proporciona una URL de base de datos
if 'RAILWAY_ENVIRONMENT' in os.environ and 'DATABASE_URL' in os.environ:
    # Obtener la URL de la base de datos proporcionada por Railway
    database_url = os.environ.get('DATABASE_URL')
    
    # Si es una URL postgres://, convertirla a postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Establecer DATABASE_URL como la URL modificada
    os.environ['DATABASE_URL'] = database_url

# Establecer ALLOWED_HOSTS para Railway
if 'RAILWAY_STATIC_URL' in os.environ:
    railway_domain = re.sub(r'^https?://', '', os.environ.get('RAILWAY_STATIC_URL'))
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
    if railway_domain and railway_domain not in allowed_hosts:
        os.environ['ALLOWED_HOSTS'] = f"{allowed_hosts},{railway_domain}" if allowed_hosts else railway_domain 