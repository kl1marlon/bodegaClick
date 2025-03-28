#!/usr/bin/env python
"""
Script para configurar OAuth 2.0 con Loyverse

Este script guía al usuario en el proceso de configuración de OAuth 2.0,
necesario para recibir correctamente el encabezado X-Loyverse-Signature
en los webhooks.

Este script no realiza la autenticación automatizada, ya que requiere
interacción del navegador, pero proporciona instrucciones detalladas.
"""

import os
import sys
import webbrowser
import re
from pathlib import Path

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta al archivo .env
ENV_FILE = os.path.join(BASE_DIR, '.env')


def update_env_file(key, value):
    """Actualiza o agrega una variable en el archivo .env"""
    # Verificar si existe el archivo .env
    if not os.path.exists(ENV_FILE):
        print(f"❌ Error: No se encontró el archivo .env en {ENV_FILE}")
        return False
    
    # Leer el contenido actual
    with open(ENV_FILE, 'r') as f:
        env_content = f.read()
    
    # Verificar si ya existe la variable
    variable_pattern = re.compile(f'^{key}=.*$', re.MULTILINE)
    
    if variable_pattern.search(env_content):
        # Reemplazar el valor existente
        new_content = variable_pattern.sub(f'{key}={value}', env_content)
    else:
        # Agregar la nueva variable al final del archivo
        if not env_content.endswith('\n'):
            env_content += '\n'
        new_content = env_content + f'{key}={value}\n'
    
    # Escribir el nuevo contenido
    with open(ENV_FILE, 'w') as f:
        f.write(new_content)
    
    return True


def open_loyverse_developer_portal():
    """Abre el portal de desarrolladores de Loyverse"""
    url = "https://developer.loyverse.com/portal"
    try:
        print(f"\n🌐 Abriendo portal de desarrolladores de Loyverse: {url}")
        webbrowser.open(url)
        return True
    except:
        print(f"\n📌 Por favor, abre manualmente este enlace: {url}")
        return False


def print_oauth_instructions():
    """Muestra instrucciones paso a paso para configurar OAuth 2.0"""
    print("\n" + "="*50)
    print("📋 Instrucciones para configurar OAuth 2.0")
    print("="*50)
    
    print("\n1️⃣ Crea una aplicación en el portal de desarrolladores:")
    print("   - Accede a https://developer.loyverse.com/portal")
    print("   - Inicia sesión con tu cuenta de Loyverse")
    print("   - Ve a 'My Applications' y crea una nueva aplicación")
    print("   - Completa la información requerida")
    
    print("\n2️⃣ Configura los permisos (scopes) necesarios:")
    print("   - Selecciona 'inventory_levels.read', 'items.read', 'webhooks.write'")
    print("   - Para más funcionalidades, añade 'items.write', 'variants.write', etc.")
    
    print("\n3️⃣ Configura la URL de redirección:")
    print("   - Añade una URL de redirección válida (puede ser http://localhost si estás en desarrollo)")
    print("   - Esta URL recibirá el código de autorización tras la aprobación")
    
    print("\n4️⃣ Obtén y guarda tus credenciales:")
    print("   - Client ID (ID de cliente)")
    print("   - Client Secret (Secreto de cliente)")
    
    print("\n5️⃣ Obtén el token de acceso:")
    print("   - Usa el flujo de autorización para obtener un token")
    print("   - Esto implica abrir una URL de autorización en tu navegador")
    print("   - Cuando se redirija, obtendrás un código que debes intercambiar por un token")
    
    print("\n6️⃣ Usa el token para crear webhooks:")
    print("   - Realiza solicitudes POST a https://api.loyverse.com/v1.0/webhooks")
    print("   - Incluye el token en el encabezado: 'Authorization: Bearer TU_TOKEN'")
    print("   - Esto garantiza que recibas el encabezado X-Loyverse-Signature en los webhooks")


def get_oauth_credentials():
    """Solicita al usuario las credenciales OAuth y las guarda en .env"""
    print("\n" + "="*50)
    print("🔐 Configuración de credenciales OAuth 2.0")
    print("="*50)
    
    # Solicitar Client ID
    client_id = input("\n👉 Ingresa tu Client ID (ID de Cliente): ").strip()
    if not client_id:
        print("❌ No se ingresó un Client ID válido. Operación cancelada.")
        return False
    
    # Solicitar Client Secret
    client_secret = input("\n👉 Ingresa tu Client Secret (Secreto de Cliente): ").strip()
    if not client_secret:
        print("❌ No se ingresó un Client Secret válido. Operación cancelada.")
        return False
    
    # Solicitar URL de redirección
    redirect_uri = input("\n👉 Ingresa tu URL de redirección: ").strip()
    if not redirect_uri:
        redirect_uri = "http://localhost"
        print(f"ℹ️ Usando URL de redirección por defecto: {redirect_uri}")
    
    # Guardar en .env
    print("\n💾 Guardando credenciales en .env...")
    update_env_file("LOYVERSE_OAUTH_CLIENT_ID", client_id)
    update_env_file("LOYVERSE_OAUTH_CLIENT_SECRET", client_secret)
    update_env_file("LOYVERSE_OAUTH_REDIRECT_URI", redirect_uri)
    
    print("✅ Credenciales guardadas correctamente.")
    
    # Construir y mostrar URL de autorización
    auth_url = f"https://api.loyverse.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=inventory_levels.read+items.read+webhooks.write+items.write"
    
    print("\n📌 Usa la siguiente URL para autorizar tu aplicación:")
    print(f"\n{auth_url}")
    
    open_url = input("\n¿Deseas abrir esta URL ahora? (s/n): ")
    if open_url.lower() == 's' or open_url.lower() == 'si' or open_url.lower() == 'sí':
        try:
            webbrowser.open(auth_url)
        except:
            print("❌ No se pudo abrir el navegador automáticamente.")
    
    print("\n📝 Después de autorizar, obtendrás un código. Úsalo para intercambiarlo por un token.")
    print("   Puedes usar el siguiente comando curl para hacerlo (reemplaza los valores):")
    
    print(f"""
curl -X POST https://api.loyverse.com/oauth/token \\
  -d "grant_type=authorization_code" \\
  -d "code=TU_CÓDIGO_AQUÍ" \\
  -d "client_id={client_id}" \\
  -d "client_secret={client_secret}" \\
  -d "redirect_uri={redirect_uri}"
    """)
    
    print("\n⚠️ Guarda el token de acceso que recibirás. Lo necesitarás para crear webhooks.")
    return True


def main():
    print("\n" + "="*50)
    print("🚀 Asistente para configuración OAuth 2.0 con Loyverse")
    print("="*50 + "\n")
    
    print("Este asistente te guiará en el proceso de configuración de OAuth 2.0,")
    print("necesario para recibir el encabezado X-Loyverse-Signature en los webhooks.")
    
    # Mostrar opciones
    print("\n🔄 Opciones disponibles:")
    print("1. Ver instrucciones detalladas para configurar OAuth 2.0")
    print("2. Abrir el portal de desarrolladores de Loyverse")
    print("3. Configurar credenciales OAuth 2.0")
    print("4. Salir")
    
    option = input("\n👉 Selecciona una opción (1-4): ")
    
    if option == '1':
        print_oauth_instructions()
    elif option == '2':
        open_loyverse_developer_portal()
    elif option == '3':
        get_oauth_credentials()
    else:
        print("\n🛑 Operación cancelada.")
    
    print("\n" + "="*50)
    print("🏁 Asistente finalizado")
    print("="*50 + "\n")


if __name__ == "__main__":
    main() 