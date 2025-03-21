FROM python:3.9-slim

# Establecer entorno para no crear archivos .pyc y mantener output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise \
    && rm -rf ~/.cache/pip

# Copiar el código del proyecto
COPY . .

# Puerto expuesto
EXPOSE 8000

# Comando por defecto (puede ser sobrescrito en docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi"] 