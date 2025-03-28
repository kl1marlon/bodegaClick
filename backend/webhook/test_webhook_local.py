#!/usr/bin/env python
"""
Script para configurar y probar webhooks con Loyverse en entorno de desarrollo local

Este script:
1. Solicita al usuario ejecutar ngrok para crear un túnel HTTPS
2. Configura y registra los webhooks con la URL de ngrok
3. Provee instrucciones para probar el funcionamiento

NOTA IMPORTANTE: Para recibir el encabezado X-Loyverse-Signature necesario para
la validación, se requiere configurar OAuth 2.0 y usar ese token para crear
los webhooks. Ver la documentación sobre OAuth 2.0 en Loyverse.

Para usar este script:
1. Asegúrate de tener ngrok instalado (https://ngrok.com/download)
2. Ejecuta este script
3. Sigue las instrucciones en pantalla
"""

import os
import sys
import django
import time
import json
import requests
import subprocess
import webbrowser

# Configurar Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.services import LoyverseService
from facturacion.models import Webhook
from django.conf import settings


def check_ngrok_running():
    """Verifica si ngrok está corriendo y obtiene la URL pública"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
        return None
    except:
        return None


def setup_ngrok():
    """Configura ngrok si no está corriendo"""
    ngrok_url = check_ngrok_running()
    
    if ngrok_url:
        print(f"✅ ngrok ya está corriendo en: {ngrok_url}")
        return ngrok_url
    
    print("\n📡 Necesitamos crear un túnel HTTPS para recibir webhooks...")
    print("⚠️ Por favor, abre una nueva terminal y ejecuta:")
    print("\nngrok http 8000\n")
    
    # En Windows, intentar abrir ngrok automáticamente si está en el PATH
    try:
        if os.name == 'nt':  # Windows
            print("🔄 Intentando iniciar ngrok automáticamente...")
            subprocess.Popen(["ngrok", "http", "8000"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
    except:
        pass
    
    input("📌 Presiona ENTER cuando hayas iniciado ngrok...")
    
    # Verificar que ngrok está corriendo
    for _ in range(5):  # intentar 5 veces
        ngrok_url = check_ngrok_running()
        if ngrok_url:
            print(f"✅ ngrok configurado correctamente en: {ngrok_url}")
            return ngrok_url
        time.sleep(2)
    
    print("❌ No se pudo detectar ngrok. Por favor verifica que está corriendo.")
    return None


def create_webhooks(base_url):
    """Crea los webhooks en Loyverse usando la URL de ngrok"""
    service = LoyverseService()
    
    # Configurar URL para recibir webhooks
    webhook_url = f"{base_url}/webhook/"
    print(f"\n🔗 Configurando webhooks hacia: {webhook_url}")
    
    # Advertencia sobre OAuth 2.0
    print("\n⚠️ IMPORTANTE: Para recibir el encabezado X-Loyverse-Signature correctamente")
    print("   se requiere configurar OAuth 2.0 y crear webhooks usando ese token.")
    print("   Este script crea webhooks con el token de API básico, lo que puede")
    print("   resultar en webhooks sin el encabezado de firma necesario para validación.")
    print("   Consulta la documentación de OAuth 2.0 de Loyverse para más detalles.")
    print("   https://developer.loyverse.com/docs/#section/Authorization/OAuth-2.0")
    
    proceed = input("\n¿Continuar con la creación de webhooks? (s/n): ")
    if proceed.lower() != 's' and proceed.lower() != 'si' and proceed.lower() != 'sí':
        print("🛑 Operación cancelada.")
        return []
    
    # Crear webhook para inventory_levels.update
    print("\n📦 Creando webhook para inventory_levels.update...")
    result_inventory = service.create_webhook(
        url=webhook_url,
        webhook_type='inventory_levels.update'
    )
    
    # Crear webhook para items.update
    print("\n📋 Creando webhook para items.update...")
    result_items = service.create_webhook(
        url=webhook_url,
        webhook_type='items.update'
    )
    
    # Verificar resultados
    webhooks_created = []
    
    if result_inventory['success']:
        webhook_data = result_inventory['webhook']
        print(f"✅ Webhook de inventario creado: {webhook_data['id']}")
        
        # Guardar en la base de datos
        Webhook.objects.create(
            id=webhook_data['id'],
            merchant_id=webhook_data['merchant_id'],
            url=webhook_data['url'],
            type=webhook_data['type'],
            status=webhook_data['status']
        )
        webhooks_created.append(webhook_data)
    else:
        print(f"❌ Error al crear webhook de inventario: {result_inventory.get('error')}")
    
    if result_items['success']:
        webhook_data = result_items['webhook']
        print(f"✅ Webhook de productos creado: {webhook_data['id']}")
        
        # Guardar en la base de datos
        Webhook.objects.create(
            id=webhook_data['id'],
            merchant_id=webhook_data['merchant_id'],
            url=webhook_data['url'],
            type=webhook_data['type'],
            status=webhook_data['status']
        )
        webhooks_created.append(webhook_data)
    else:
        print(f"❌ Error al crear webhook de productos: {result_items.get('error')}")
    
    return webhooks_created


def test_webhooks():
    """Proporciona instrucciones para probar los webhooks"""
    print("\n🧪 Instrucciones para probar los webhooks:")
    print("\n1️⃣ Para probar el webhook de inventory_levels.update:")
    print("   - Ve a tu cuenta de Loyverse")
    print("   - Modifica el inventario de algún producto")
    print("   - Observa los logs del servidor Django para ver la notificación")
    
    print("\n2️⃣ Para probar el webhook de items.update:")
    print("   - Ve a tu cuenta de Loyverse")
    print("   - Crea un nuevo producto o modifica uno existente")
    print("   - Observa los logs del servidor Django para ver la notificación")
    
    print("\n⚠️ Importante: Verifica si estás recibiendo el encabezado X-Loyverse-Signature")
    print("   Si no lo recibes, deberás usar OAuth 2.0 para crear los webhooks.")
    
    print("\n⚠️ Importante: Los webhooks dejarán de funcionar cuando detengas ngrok.")
    print("   En un entorno de producción, necesitarás una URL HTTPS permanente.")


def open_loyverse_dashboard():
    """Abre el dashboard de Loyverse para facilitar las pruebas"""
    try:
        print("\n🌐 Abriendo el dashboard de Loyverse para facilitar las pruebas...")
        webbrowser.open("https://pos.loyverse.com/dashboard")
    except:
        print("\n🔗 Puedes abrir manualmente el dashboard de Loyverse en: https://pos.loyverse.com/dashboard")


def main():
    print("\n" + "="*50)
    print("🚀 Asistente de configuración de Webhooks para Loyverse")
    print("="*50 + "\n")
    
    # Verificar token de API
    if not settings.LOYVERSE_API_TOKEN:
        print("❌ Error: No se ha configurado LOYVERSE_API_TOKEN en settings")
        return
    
    # Verificar secreto de webhook
    if not settings.LOYVERSE_WEBHOOK_SECRET:
        print("⚠️ Advertencia: No se ha configurado LOYVERSE_WEBHOOK_SECRET")
        print("   Se recomienda configurarlo para validar la autenticidad de los webhooks")
        
        set_secret = input("¿Deseas generar un secreto ahora? (s/n): ")
        if set_secret.lower() == 's' or set_secret.lower() == 'si' or set_secret.lower() == 'sí':
            # Importar el módulo para generar secreto
            sys.path.insert(0, os.path.dirname(__file__))
            import update_webhook_secret
            update_webhook_secret.main()
    
    # Configurar ngrok
    ngrok_url = setup_ngrok()
    if not ngrok_url:
        return
    
    # Crear webhooks
    webhooks = create_webhooks(ngrok_url)
    
    # Si se crearon webhooks, dar instrucciones
    if webhooks:
        print("\n✅ Webhooks configurados correctamente!")
        test_webhooks()
        open_loyverse_dashboard()
    
    print("\n" + "="*50)
    print("🏁 Configuración completa")
    print("="*50 + "\n")


if __name__ == "__main__":
    main() 