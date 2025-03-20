#!/usr/bin/env python
"""
Script para crear un webhook de inventory_levels.update en Loyverse

Este script utiliza la API de Loyverse para crear un webhook que notificará
sobre cambios en el inventario.
"""

import os
import sys
import django
import argparse

# Configurar Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.services import LoyverseService
from facturacion.models import Webhook
from django.conf import settings
import uuid


def create_inventory_webhook(webhook_url=None):
    """
    Crea un webhook para inventory_levels.update en Loyverse
    """
    # Si no se proporciona URL, usar la URL de la aplicación + /webhook/
    if not webhook_url:
        print("Error: Debe proporcionar una URL para el webhook")
        print("Ejemplo: python create_webhook.py --url https://miapp.com/webhook/")
        return False
    
    # Verificar que la URL use HTTPS
    if not webhook_url.startswith('https://'):
        print("Error: La URL del webhook debe usar HTTPS")
        return False
    
    service = LoyverseService()
    
    # Crear el webhook en Loyverse
    result = service.create_webhook(
        url=webhook_url,
        webhook_type='inventory_levels.update'
    )
    
    if result['success']:
        webhook_data = result['webhook']
        print(f"Webhook creado correctamente:")
        print(f"ID: {webhook_data['id']}")
        print(f"URL: {webhook_data['url']}")
        print(f"Tipo: {webhook_data['type']}")
        print(f"Estado: {webhook_data['status']}")
        
        # Guardar en la base de datos local
        Webhook.objects.create(
            id=webhook_data['id'],
            merchant_id=webhook_data['merchant_id'],
            url=webhook_data['url'],
            type=webhook_data['type'],
            status=webhook_data['status']
        )
        
        print("Webhook guardado en la base de datos local")
        return True
    else:
        print(f"Error al crear webhook: {result['error']}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crear webhook de inventario en Loyverse')
    parser.add_argument('--url', type=str, help='URL del webhook (debe usar HTTPS)')
    
    args = parser.parse_args()
    
    create_inventory_webhook(args.url) 