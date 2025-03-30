from django.core.management.base import BaseCommand
import requests
from facturacion.models import Producto
from django.conf import settings
import time
import datetime
import sys

class Command(BaseCommand):
    help = 'Sincroniza el inventario de los productos con Loyverse, obteniendo el stock actual y actualizando los variant_id faltantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la actualización de todos los productos, incluso los que ya tienen stock',
        )

    def handle(self, *args, **options):
        # Configuración de la API
        BASE_URL = 'https://api.loyverse.com/v1.0'
        headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Parámetros
        force = options['force']
        
        # ID específico de la tienda principal
        store_id = '8aa31f38-96ee-4887-ad51-0362dfa034e6'
        
        # Filtrar productos según la bandera --force
        if force:
            productos = Producto.objects.filter(loyverse_id__isnull=False)
            self.stdout.write(f"Procesando TODOS los productos con loyverse_id ({productos.count()})")
        else:
            # Solo productos sin stock actual o con variant_id faltante
            productos = Producto.objects.filter(
                loyverse_id__isnull=False
            ).filter(
                stock_actual=0
            )
            self.stdout.write(f"Procesando productos sin stock actual ({productos.count()})")
        
        # Estadísticas
        total_productos = productos.count()
        productos_actualizados = 0
        productos_con_error = 0
        productos_sin_variant = 0
        productos_con_inventory = 0
        
        # Procesar cada producto
        for i, producto in enumerate(productos):
            self.stdout.write(f"\nProcesando {i+1}/{total_productos}: {producto.nombre}")
            
            # Paso 1: Asegurar que tenemos el variant_id
            variant_id = producto.variant_id
            if not variant_id:
                try:
                    # Consultar la API de Loyverse para obtener los detalles del producto
                    item_url = f"{BASE_URL}/items/{producto.loyverse_id}"
                    self.stdout.write(f"  Producto sin variant_id, consultando: {item_url}")
                    
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
                                f"  ✅ Actualizado variant_id: {variant_id}"
                            ))
                            productos_sin_variant += 1
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"  ⚠️ Producto no tiene variantes en Loyverse"
                            ))
                            productos_con_error += 1
                            continue  # Seguir con el siguiente producto
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"  ❌ Error al consultar producto: {response.status_code} - {response.text}"
                        ))
                        productos_con_error += 1
                        continue  # Seguir con el siguiente producto
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ Error procesando producto: {str(e)}"
                    ))
                    productos_con_error += 1
                    continue  # Seguir con el siguiente producto
            
            # Paso 2: Consultar el inventario actual
            try:
                inventory_url = f"{BASE_URL}/inventory?variant_ids={variant_id}"
                self.stdout.write(f"  Consultando inventario: {inventory_url}")
                
                inventory_response = requests.get(inventory_url, headers=headers)
                
                if inventory_response.status_code == 200:
                    inventory_data = inventory_response.json()
                    inventory_levels = inventory_data.get('inventory_levels', [])
                    
                    # Buscar el nivel de inventario para la tienda principal
                    current_stock = 0
                    for level in inventory_levels:
                        if level.get('store_id') == store_id and level.get('variant_id') == variant_id:
                            current_stock = level.get('in_stock', 0)
                            break
                    
                    # Actualizar el stock en la base de datos local
                    producto.stock_actual = current_stock
                    producto.ultima_actualizacion_stock = datetime.datetime.now()
                    producto.save(update_fields=['stock_actual', 'ultima_actualizacion_stock'])
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Stock actualizado: {current_stock} unidades"
                    ))
                    productos_actualizados += 1
                    productos_con_inventory += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ Error al consultar inventario: {inventory_response.status_code} - {inventory_response.text}"
                    ))
                    productos_con_error += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  ❌ Error consultando inventario: {str(e)}"
                ))
                productos_con_error += 1
            
            # Esperar un poco entre peticiones para evitar límites de API
            if (i + 1) % 5 == 0:
                self.stdout.write(f"  Esperando 1 segundo... ({i+1}/{total_productos})")
                time.sleep(1)
        
        # Resumen final
        self.stdout.write("\n")
        self.stdout.write(self.style.SUCCESS("=== RESUMEN DE SINCRONIZACIÓN DE INVENTARIO ==="))
        self.stdout.write(f"Total productos procesados: {total_productos}")
        self.stdout.write(self.style.SUCCESS(f"Productos con stock actualizado: {productos_actualizados}"))
        self.stdout.write(self.style.SUCCESS(f"Productos con variant_id añadido: {productos_sin_variant}"))
        self.stdout.write(self.style.SUCCESS(f"Productos con información de inventario: {productos_con_inventory}"))
        self.stdout.write(self.style.ERROR(f"Productos con error: {productos_con_error}")) 