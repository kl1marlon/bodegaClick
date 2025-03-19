import requests
from django.conf import settings
from .models import Producto

class LoyverseService:
    BASE_URL = 'https://api.loyverse.com/v1.0'
    
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def fetch_products(self):
        """
        Obtiene todos los productos de Loyverse y los almacena en la base de datos local
        """
        url = f"{self.BASE_URL}/items"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            items = response.json().get('items', [])
            products_created = 0
            products_updated = 0
            
            for item in items:
                # Tomamos el primer variante como precio base
                if item.get('variants'):
                    variant = item['variants'][0]
                    precio = variant.get('default_price', 0)
                else:
                    precio = 0
                
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
                else:
                    products_updated += 1
            
            return {
                'success': True,
                'created': products_created,
                'updated': products_updated
            }
        
        return {
            'success': False,
            'error': f'Error al obtener productos: {response.status_code}'
        }

    def sync_prices(self, products):
        """
        Sincroniza los precios de los productos con Loyverse
        """
        for product in products:
            variant_id = None
            # Obtener el ID del variante
            url = f"{self.BASE_URL}/items/{product.loyverse_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                item_data = response.json()
                if item_data.get('variants'):
                    variant_id = item_data['variants'][0]['variant_id']
                    
                    # Actualizar precio
                    update_url = f"{self.BASE_URL}/variants/{variant_id}"
                    update_data = {
                        'default_price': float(product.precio_base)
                    }
                    
                    update_response = requests.put(
                        update_url,
                        headers=self.headers,
                        json=update_data
                    )
                    
                    if update_response.status_code != 200:
                        return {
                            'success': False,
                            'error': f'Error al actualizar precio: {update_response.status_code}'
                        }
        
        return {'success': True} 