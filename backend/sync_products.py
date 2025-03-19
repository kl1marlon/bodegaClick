import os
import django
import requests
from decimal import Decimal
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Producto

def sync_products():
    """Sincronizar productos desde Loyverse"""
    api_token = os.environ.get('LOYVERSE_API_TOKEN')
    if not api_token:
        print("❌ No se encontró el token de Loyverse")
        return

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    products_created = 0
    products_updated = 0
    cursor = None
    page = 1

    try:
        while True:
            print(f"\n📃 Procesando página {page}...")
            
            # Construir URL con cursor si existe
            url = 'https://api.loyverse.com/v1.0/items'
            if cursor:
                url += f'?cursor={cursor}'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break  # No hay más productos para procesar
                
                for item in items:
                    try:
                        # Obtener el precio del primer variante
                        precio = Decimal('0')
                        if item.get('variants'):
                            variant = item['variants'][0]
                            precio_str = str(variant.get('default_price', '0'))
                            # Asegurarse de que el precio sea un número válido
                            try:
                                precio = Decimal(precio_str)
                            except:
                                print(f"⚠️ Precio inválido para {item['item_name']}: {precio_str}")
                                precio = Decimal('0')
                        
                        # Crear o actualizar el producto
                        producto, created = Producto.objects.update_or_create(
                            loyverse_id=item['id'],
                            defaults={
                                'nombre': item['item_name'],
                                'descripcion': item.get('description', ''),
                                'precio_base': precio
                            }
                        )
                        
                        if created:
                            products_created += 1
                            print(f"✨ Nuevo producto: {item['item_name']}")
                        else:
                            products_updated += 1
                            print(f"📝 Actualizado: {item['item_name']}")
                    except Exception as e:
                        print(f"⚠️ Error procesando producto {item.get('item_name', 'desconocido')}:")
                        print(f"   {str(e)}")
                        continue
                
                # Obtener el cursor para la siguiente página
                cursor = data.get('cursor')
                if not cursor:
                    break  # No hay más páginas para procesar
                
                page += 1
                # Pequeña pausa para evitar sobrecargar la API
                time.sleep(0.5)
                
            else:
                print("❌ Error conectando a Loyverse:")
                print(f"Status code: {response.status_code}")
                print(f"Response: {response.text}")
                break
    
    except Exception as e:
        print("❌ Error durante la sincronización:")
        print(str(e))
    
    print(f"\n✅ Sincronización completada:")
    print(f"   - Páginas procesadas: {page}")
    print(f"   - Productos creados: {products_created}")
    print(f"   - Productos actualizados: {products_updated}")
    print(f"   - Total productos: {products_created + products_updated}")

if __name__ == '__main__':
    print("=== Iniciando sincronización de productos ===\n")
    sync_products() 