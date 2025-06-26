FROM python:3.9-alpine

# Establecer variables de entorno básicas
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Copiar solo el archivo de requisitos mínimos
COPY requirements-minimal.txt .

# Instalar dependencias mínimas
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Crear un archivo simple para health check
RUN echo 'from django.http import JsonResponse\n\ndef health_check(request):\n    return JsonResponse({"status": "ok"})' > health.py

# Crear un archivo mínimo para iniciar
RUN echo '#!/bin/sh\necho "Servidor de recuperación iniciado"\npython -m http.server $PORT' > start.sh && chmod +x start.sh

EXPOSE $PORT
CMD ["/app/start.sh"] 