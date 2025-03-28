#!/usr/bin/env python
"""
Script para limpiar y eliminar webhooks de Loyverse

Este script lista todos los webhooks registrados en Loyverse y permite
eliminarlos, tanto de la API de Loyverse como de la base de datos local.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.services import LoyverseService
from facturacion.models import Webhook


def list_webhooks():
    """Lista todos los webhooks registrados en Loyverse"""
    service = LoyverseService()
    result = service.list_webhooks()
    
    if not result['success']:
        print(f"❌ Error al listar webhooks: {result.get('error')}")
        return None
    
    webhooks = result['webhooks']
    
    if not webhooks:
        print("ℹ️ No hay webhooks registrados en Loyverse.")
        return []
    
    print("\n📋 Webhooks registrados en Loyverse:")
    for i, webhook in enumerate(webhooks, 1):
        print(f"\n{i}. ID: {webhook['id']}")
        print(f"   URL: {webhook['url']}")
        print(f"   Tipo: {webhook['type']}")
        print(f"   Estado: {webhook['status']}")
    
    return webhooks


def delete_webhook(webhook_id, delete_from_db=True):
    """Elimina un webhook de Loyverse y opcionalmente de la base de datos local"""
    service = LoyverseService()
    result = service.delete_webhook(webhook_id)
    
    if result['success']:
        print(f"✅ Webhook {webhook_id} eliminado de Loyverse.")
        
        if delete_from_db:
            try:
                webhook = Webhook.objects.get(id=webhook_id)
                webhook.delete()
                print(f"✅ Webhook {webhook_id} eliminado de la base de datos local.")
            except Webhook.DoesNotExist:
                print(f"⚠️ El webhook {webhook_id} no existe en la base de datos local.")
        
        return True
    else:
        print(f"❌ Error al eliminar webhook {webhook_id}: {result.get('error')}")
        return False


def cleanup_all_webhooks():
    """Elimina todos los webhooks registrados en Loyverse"""
    webhooks = list_webhooks()
    
    if not webhooks:
        return
    
    confirmation = input("\n⚠️ ¿Estás seguro de que deseas eliminar TODOS los webhooks? (s/n): ")
    
    if confirmation.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print("🛑 Operación cancelada.")
        return
    
    deleted_count = 0
    for webhook in webhooks:
        if delete_webhook(webhook['id']):
            deleted_count += 1
    
    print(f"\n🧹 Se han eliminado {deleted_count} de {len(webhooks)} webhooks.")


def main():
    print("\n" + "="*50)
    print("🧹 Limpieza de Webhooks para Loyverse")
    print("="*50 + "\n")
    
    # Listar webhooks
    webhooks = list_webhooks()
    
    if webhooks is None:  # Error al listar
        return
    
    if not webhooks:  # No hay webhooks
        print("✅ No hay webhooks que eliminar.")
        return
    
    print("\n🔄 Opciones disponibles:")
    print("1. Eliminar un webhook específico")
    print("2. Eliminar todos los webhooks")
    print("3. Salir sin hacer cambios")
    
    option = input("\n👉 Selecciona una opción (1-3): ")
    
    if option == '1':
        webhook_index = input(f"\n👉 Ingresa el número del webhook a eliminar (1-{len(webhooks)}): ")
        try:
            index = int(webhook_index) - 1
            if 0 <= index < len(webhooks):
                delete_webhook(webhooks[index]['id'])
            else:
                print("❌ Índice inválido.")
        except ValueError:
            print("❌ Entrada inválida.")
    elif option == '2':
        cleanup_all_webhooks()
    else:
        print("🛑 Operación cancelada.")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main() 