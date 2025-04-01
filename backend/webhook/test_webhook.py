#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para simular webhooks de Loyverse y probar la recepción en tu aplicación.
Útil para verificar que tu aplicación está lista para recibir webhooks reales.
"""

import argparse
import json
import hmac
import hashlib
import requests
import sys
import base64

def simulate_webhook(url, event_type, secret, payload=None):
    """
    Simula el envío de un webhook desde Loyverse a tu aplicación.
    
    Args:
        url (str): URL del webhook (tu endpoint receptor)
        event_type (str): Tipo de evento (inventory_levels.update o items.update)
        secret (str): Secreto para firmar el webhook
        payload (dict): Datos a enviar (si no se especifica, se usa un ejemplo)
    
    Returns:
        dict: Respuesta de tu aplicación al webhook
    """
    # Usar payload proporcionado o ejemplos predefinidos
    if not payload:
        if event_type == "inventory_levels.update":
            payload = {
                "merchant_id": "5fk4f446-01d2-8787-4fd5-7b7b1995df85",
                "type": "inventory_levels.update",
                "created_at": "2025-03-28T12:00:00.000Z",
                "inventory_levels": [
                    {
                        "store_id": "12345678-1234-1234-1234-1234567890ab",
                        "variant_id": "abcdef12-1234-5678-90ab-cdef12345678",
                        "in_stock": 50,
                        "updated_at": "2025-03-28T12:00:00.000Z"
                    }
                ]
            }
        elif event_type == "items.update":
            payload = {
                "merchant_id": "5fk4f446-01d2-8787-4fd5-7b7b1995df85",
                "type": "items.update",
                "created_at": "2025-03-28T12:00:00.000Z",
                "items": [
                    {
                        "id": "12345678-1234-1234-1234-1234567890ab",
                        "updated_at": "2025-03-28T12:00:00.000Z"
                    }
                ]
            }
    
    # Convertir payload a JSON
    body = json.dumps(payload).encode('utf-8')
    
    # Generar firma con HMAC-SHA1 en base64 según la documentación de Loyverse
    signature = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    # Configurar headers
    headers = {
        "Content-Type": "application/json",
        "X-Loyverse-Event": event_type,
        "X-Loyverse-Signature": signature,
        "X-Loyverse-API-version": "v1.0"
    }
    
    print(f"\n🔹 Simulando webhook de tipo '{event_type}'")
    print(f"URL: {url}")
    print(f"Firma (base64): {signature}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Enviar solicitud
        response = requests.post(url, headers=headers, data=body)
        
        print(f"\nRespuesta HTTP: {response.status_code}")
        print(f"Contenido: {response.text[:1000]}")  # Mostrar los primeros 1000 caracteres
        
        return {
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "response": response.text
        }
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error al enviar webhook: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='Simular webhooks de Loyverse')
    
    parser.add_argument('--url', required=True,
                        help='URL donde enviar el webhook simulado')
    
    parser.add_argument('--type', required=True, choices=['inventory_levels.update', 'items.update'],
                        help='Tipo de evento a simular')
    
    parser.add_argument('--secret', required=True,
                        help='Secreto para firmar el webhook')
    
    parser.add_argument('--payload', 
                        help='Archivo JSON con los datos a enviar (opcional)')
    
    args = parser.parse_args()
    
    # Cargar payload desde archivo si se especifica
    payload = None
    if args.payload:
        try:
            with open(args.payload) as f:
                payload = json.load(f)
        except Exception as e:
            print(f"Error al leer archivo de payload: {e}")
            return
    
    # Simular webhook
    result = simulate_webhook(args.url, args.type, args.secret, payload)
    
    if result["success"]:
        print("\n✅ Webhook simulado enviado exitosamente.")
        print("\nVerifica los logs de tu aplicación para confirmar que se procesó correctamente.")
    else:
        print("\n❌ Error al simular webhook.")
        print("Asegúrate de que tu aplicación esté en ejecución y sea accesible en la URL especificada.")
        sys.exit(1)

if __name__ == "__main__":
    main() 