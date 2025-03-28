FROM python:3.9-slim

# Establecer entorno para no crear archivos .pyc y mantener output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar todo el código primero para asegurar que requirements.txt esté disponible
COPY . /app/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

EXPOSE 8000 

# Comando para iniciar la aplicación
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]