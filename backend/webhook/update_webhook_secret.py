#!/usr/bin/env python
"""
Script para actualizar el secreto del webhook en el archivo .env

Este script genera un nuevo secreto aleatorio y lo guarda en el archivo .env,
que será utilizado para verificar la autenticidad de los webhooks recibidos.
"""

import os
import sys
import secrets
import string
import re
from pathlib import Path

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta al archivo .env
ENV_FILE = os.path.join(BASE_DIR, '.env')


def generate_secure_secret(length=64):
    """Genera un secreto seguro de la longitud especificada"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def update_env_file(new_secret):
    """Actualiza o agrega el secreto en el archivo .env"""
    # Verificar si existe el archivo .env
    if not os.path.exists(ENV_FILE):
        print(f"❌ Error: No se encontró el archivo .env en {ENV_FILE}")
        return False
    
    # Leer el contenido actual
    with open(ENV_FILE, 'r') as f:
        env_content = f.read()
    
    # Verificar si ya existe la variable LOYVERSE_WEBHOOK_SECRET
    webhook_secret_pattern = re.compile(r'^LOYVERSE_WEBHOOK_SECRET=.*$', re.MULTILINE)
    
    if webhook_secret_pattern.search(env_content):
        # Reemplazar el valor existente
        new_content = webhook_secret_pattern.sub(f'LOYVERSE_WEBHOOK_SECRET={new_secret}', env_content)
    else:
        # Agregar la nueva variable al final del archivo
        if not env_content.endswith('\n'):
            env_content += '\n'
        new_content = env_content + f'LOYVERSE_WEBHOOK_SECRET={new_secret}\n'
    
    # Escribir el nuevo contenido
    with open(ENV_FILE, 'w') as f:
        f.write(new_content)
    
    return True


def main():
    print("\n" + "="*50)
    print("🔐 Actualizando el secreto del webhook para Loyverse")
    print("="*50 + "\n")
    
    # Generar un nuevo secreto seguro
    new_secret = generate_secure_secret()
    print(f"🔑 Nuevo secreto generado: {new_secret}")
    
    # Actualizar el archivo .env
    if update_env_file(new_secret):
        print(f"✅ Secreto actualizado correctamente en {ENV_FILE}")
        print("\n⚠️ Importante: Debes reiniciar el servidor Django para aplicar los cambios.")
    else:
        print("❌ No se pudo actualizar el secreto.")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main() 