#!/usr/bin/env python
"""
Script para crear webhooks usando OAuth 2.0

Este script crea webhooks de Loyverse usando un token OAuth 2.0,
lo que garantiza que se reciba el encabezado X-Loyverse-Signature
necesario para la validación de firma en las notificaciones.

Uso:
  python create_webhook_oauth.py --url URL --type TIPO --token TOKEN
"""

import os
import sys
import argparse
import requests
import django

# Configurar Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Webhook


def create_webhook_with_oauth(webhook_url, webhook_type, oauth_token):
    """
    Crea un webhook usando un token OAuth 2.0
    
    Args:
        webhook_url (str): URL donde se enviarán las notificaciones
        webhook_type (str): Tipo de webhook (inventory_levels.update, items.update, etc.)
        oauth_token (str): Token OAuth 2.0 obtenido previamente
    
    Returns:
        dict: Resultado de la operación
    """
    # Validar parámetros
    if not webhook_url:
        return {
            'success': False,
            'error': 'Se requiere una URL para el webhook'
        }
    
    if not webhook_type:
        return {
            'success': False,
            'error': 'Se requiere un tipo de webhook'
        }
    
    if not oauth_token:
        return {
            'success': False,
            'error': 'Se requiere un token OAuth 2.0'
        }
    
    # Verificar HTTPS en producción
    if not webhook_url.startswith('https://') and not webhook_url.startswith('http://localhost'):
        print("⚠️ Advertencia: La URL del webhook debería usar HTTPS en producción.")
    
    # Endpoint para crear webhooks
    webhook_url_api = "https://api.loyverse.com/v1.0/webhooks"
    
    # Payload con datos del webhook
    payload = {
        'url': webhook_url,
        'type': webhook_type
    }
    
    # Headers con autorización OAuth 2.0
    headers = {
        'Authorization': f'Bearer {oauth_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Realizar la solicitud para crear el webhook
        response = requests.post(webhook_url_api, json=payload, headers=headers)
        
        # Verificar respuesta
        if response.status_code == 200:
            webhook_data = response.json()
            
            # Guardar en la base de datos local
            try:
                Webhook.objects.create(
                    id=webhook_data['id'],
                    merchant_id=webhook_data['merchant_id'],
                    url=webhook_data['url'],
                    type=webhook_data['type'],
                    status=webhook_data['status']
                )
                print("✅ Webhook guardado en la base de datos local")
            except Exception as e:
                print(f"⚠️ Error al guardar webhook en la base de datos: {str(e)}")
            
            return {
                'success': True,
                'webhook': webhook_data
            }
        else:
            error_message = f"Error al crear webhook: {response.status_code}"
            try:
                error_detail = response.json()
                error_message += f" - {error_detail.get('message', '')}"
            except:
                pass
            
            return {
                'success': False,
                'error': error_message,
                'response': response.text
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"Excepción al crear webhook: {str(e)}"
        }


def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Crear webhook usando OAuth 2.0')
    parser.add_argument('--url', type=str, help='URL del webhook (debe usar HTTPS en producción)')
    parser.add_argument('--type', type=str, choices=['inventory_levels.update', 'items.update'], 
                       help='Tipo de webhook: inventory_levels.update o items.update')
    parser.add_argument('--token', type=str, help='Token OAuth 2.0')
    
    args = parser.parse_args()
    
    # Verificar si se proporcionaron todos los argumentos requeridos
    if not all([args.url, args.type, args.token]):
        print("❌ Error: Se requieren todos los argumentos: --url, --type y --token")
        print("Ejemplo: python create_webhook_oauth.py --url https://miapp.com/webhook/ --type inventory_levels.update --token mi_token_oauth")
        return
    
    print(f"🔄 Creando webhook {args.type} hacia {args.url} con OAuth...")
    
    # Crear el webhook
    result = create_webhook_with_oauth(args.url, args.type, args.token)
    
    if result['success']:
        webhook_data = result['webhook']
        print(f"✅ Webhook creado correctamente:")
        print(f"ID: {webhook_data['id']}")
        print(f"URL: {webhook_data['url']}")
        print(f"Tipo: {webhook_data['type']}")
        print(f"Estado: {webhook_data['status']}")
    else:
        print(f"❌ Error al crear webhook: {result['error']}")


if __name__ == "__main__":
    main() 