import os
import django
import requests
import os
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Producto, TasaCambio

def test_database():
    """Probar la conexión a la base de datos"""
    try:
        # Intentar crear una tasa de cambio de prueba
        tasa = TasaCambio.objects.create(
            tipo='BCV',
            valor=Decimal('35.50')
        )
        print("✅ Conexión a la base de datos exitosa")
        print(f"Tasa de prueba creada: {tasa}")
        return True
    except Exception as e:
        print("❌ Error conectando a la base de datos:")
        print(str(e))
        return False

def test_loyverse():
    """Probar la conexión a Loyverse"""
    api_token = os.environ.get('LOYVERSE_API_TOKEN')
    print(f"Token de Loyverse: {api_token}")
    if not api_token:
        print("❌ No se encontró el token de Loyverse")
        return False

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            'https://api.loyverse.com/v1.0/items',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Conexión a Loyverse exitosa")
            print(f"Productos encontrados: {len(data.get('items', []))}")
            return True
        else:
            print("❌ Error conectando a Loyverse:")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print("❌ Error conectando a Loyverse:")
        print(str(e))
        return False

if __name__ == '__main__':
    print("=== Probando conexiones ===")
    print("\n1. Probando base de datos PostgreSQL...")
    db_ok = test_database()
    
    print("\n2. Probando API de Loyverse...")
    loyverse_ok = test_loyverse()
    
    if db_ok and loyverse_ok:
        print("\n✅ Todo está configurado correctamente!")
    else:
        print("\n❌ Hay errores que necesitan ser corregidos") 