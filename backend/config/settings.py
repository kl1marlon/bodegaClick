import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))

# Cargar configuración específica de Railway
try:
    from ..railway_settings import *
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'

# Configurar DEBUG según el entorno
DEBUG = os.environ.get('RAILWAY_ENVIRONMENT', '').lower() != 'true'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'facturacion',
    # 'channels',  # Comentado temporalmente
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Añadir whitenoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:3000$",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Configuración de base de datos
# Si DATABASE_URL está presente (Railway), usar dj-database-url
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    # Imprimir información de debug
    print(f"Usando DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
# Si tenemos variables PGHOST, PGUSER, etc. de Railway, usarlas directamente
elif all(env_var in os.environ for env_var in ['PGHOST', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']):
    print("Usando variables PG* directamente")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('PGDATABASE'),
            'USER': os.environ.get('PGUSER'),
            'PASSWORD': os.environ.get('PGPASSWORD'),
            'HOST': os.environ.get('PGHOST'),
            'PORT': os.environ.get('PGPORT', '5432'),
        }
    }
# Si DATABASE_PUBLIC_URL está presente, usarla
elif 'DATABASE_PUBLIC_URL' in os.environ:
    import dj_database_url
    print(f"Usando DATABASE_PUBLIC_URL: {os.environ.get('DATABASE_PUBLIC_URL')}")
    # Configurar la URL de la base de datos pública
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = database_url
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
else:
    # Configuración local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'facturacion_db'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-ve'

TIME_ZONE = 'America/Caracas'

USE_I18N = True

USE_TZ = True

# Configuración de archivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Loyverse API Configuration
LOYVERSE_API_TOKEN = os.environ.get('LOYVERSE_API_TOKEN', '')
LOYVERSE_MERCHANT_ID = os.environ.get('LOYVERSE_MERCHANT_ID', '')
LOYVERSE_WEBHOOK_SECRET = os.environ.get('LOYVERSE_WEBHOOK_SECRET', '')
if not LOYVERSE_API_TOKEN:
    raise ValueError('LOYVERSE_API_TOKEN must be set in environment variables')

# Channels Configuration
# ASGI_APPLICATION = 'config.asgi.application'
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer',
#     },
# } 