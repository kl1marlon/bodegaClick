from django.core.management.base import BaseCommand
import requests
from facturacion.models import Producto
from django.conf import settings
import time

class Command(BaseCommand):
    help = 'Actualiza los variant_id de productos existentes consultando la API de Loyverse'

    def handle(self, *args, **options):
        # Configuración de la API
        BASE_URL = 'https://api.loyverse.com/v1.0'
        headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Obtener productos sin variant_id
        productos_sin_variant_id = Producto.objects.filter(
            loyverse_id__isnull=False, 
            variant_id__isnull=True
        )
        
        total_productos = productos_sin_variant_id.count()
        productos_actualizados = 0
        productos_con_error = 0
        
        self.stdout.write(f"Encontrados {total_productos} productos sin variant_id")
        
        # Procesar en grupos de 10 para evitar límites de API
        for i, producto in enumerate(productos_sin_variant_id):
            try:
                # Consultar la API de Loyverse para obtener los detalles del producto
                item_url = f"{BASE_URL}/items/{producto.loyverse_id}"
                self.stdout.write(f"Consultando producto {i+1}/{total_productos}: {producto.nombre}")
                
                response = requests.get(item_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar si el producto tiene variantes
                    if 'variants' in data and len(data['variants']) > 0:
                        variant_id = data['variants'][0]['variant_id']
                        
                        # Actualizar el producto con el variant_id
                        producto.variant_id = variant_id
                        producto.save(update_fields=['variant_id'])
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Actualizado producto {producto.nombre}: variant_id={variant_id}"
                        ))
                        productos_actualizados += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Producto {producto.nombre} no tiene variantes en Loyverse"
                        ))
                        productos_con_error += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error al consultar producto {producto.nombre}: {response.status_code} - {response.text}"
                    ))
                    productos_con_error += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Error procesando producto {producto.nombre}: {str(e)}"
                ))
                productos_con_error += 1
            
            # Esperar un poco entre peticiones para evitar límites de API
            if (i + 1) % 10 == 0:
                self.stdout.write(f"Esperando 2 segundos... ({i+1}/{total_productos})")
                time.sleep(2)
        
        # Resumen final
        self.stdout.write("\n")
        self.stdout.write(self.style.SUCCESS("=== RESUMEN ==="))
        self.stdout.write(f"Total productos procesados: {total_productos}")
        self.stdout.write(self.style.SUCCESS(f"Productos actualizados: {productos_actualizados}"))
        self.stdout.write(self.style.ERROR(f"Productos con error: {productos_con_error}")) 