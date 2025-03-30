from django.core.management.base import BaseCommand
import requests
from facturacion.models import Producto
from django.conf import settings
import time
import datetime
import sys

class Command(BaseCommand):
    help = 'Sincroniza el inventario de los productos con Loyverse'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la actualizacion de todos los productos',
        )

    def handle(self, *args, **options):
        # Configuracion de la API
        BASE_URL = 'https://api.loyverse.com/v1.0'
        headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Parametros
        force = options['force']
        
        # ID de la tienda principal
        store_id = '8aa31f38-96ee-4887-ad51-0362dfa034e6'
        
        # Filtrar productos segun --force
        if force:
            productos = Producto.objects.filter(loyverse_id__isnull=False)
            self.stdout.write(f"Procesando TODOS los productos ({productos.count()})")
        else:
            # Solo productos sin stock
            productos = Producto.objects.filter(
                loyverse_id__isnull=False,
                stock_actual=0
            )
            self.stdout.write(f"Procesando productos sin stock ({productos.count()})")
        
        # Estadisticas
        total_productos = productos.count()
        productos_actualizados = 0
        productos_con_error = 0
        productos_sin_variant = 0
        productos_con_inventory = 0
        
        # Procesar cada producto
        for i, producto in enumerate(productos):
            self.stdout.write(f"Procesando {i+1}/{total_productos}: {producto.nombre}")
            
            # Paso 1: Obtener variant_id si no existe
            variant_id = producto.variant_id
            if not variant_id:
                try:
                    item_url = f"{BASE_URL}/items/{producto.loyverse_id}"
                    self.stdout.write(f"Consultando producto: {item_url}")
                    
                    response = requests.get(item_url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'variants' in data and len(data['variants']) > 0:
                            variant_id = data['variants'][0]['variant_id']
                            
                            producto.variant_id = variant_id
                            producto.save(update_fields=['variant_id'])
                            
                            self.stdout.write(f"Variant ID actualizado: {variant_id}")
                            productos_sin_variant += 1
                        else:
                            self.stdout.write(f"Producto sin variantes en Loyverse")
                            productos_con_error += 1
                            continue
                    else:
                        self.stdout.write(f"Error consultando producto: {response.status_code}")
                        productos_con_error += 1
                        continue
                
                except Exception as e:
                    self.stdout.write(f"Error procesando producto: {str(e)}")
                    productos_con_error += 1
                    continue
            
            # Paso 2: Consultar inventario
            try:
                inventory_url = f"{BASE_URL}/inventory?variant_ids={variant_id}"
                self.stdout.write(f"Consultando inventario: {inventory_url}")
                
                inventory_response = requests.get(inventory_url, headers=headers)
                
                if inventory_response.status_code == 200:
                    inventory_data = inventory_response.json()
                    inventory_levels = inventory_data.get('inventory_levels', [])
                    
                    current_stock = 0
                    for level in inventory_levels:
                        if level.get('store_id') == store_id and level.get('variant_id') == variant_id:
                            current_stock = level.get('in_stock', 0)
                            break
                    
                    producto.stock_actual = current_stock
                    producto.ultima_actualizacion_stock = datetime.datetime.now()
                    producto.save(update_fields=['stock_actual', 'ultima_actualizacion_stock'])
                    
                    self.stdout.write(f"Stock actualizado: {current_stock} unidades")
                    productos_actualizados += 1
                    productos_con_inventory += 1
                else:
                    self.stdout.write(f"Error consultando inventario: {inventory_response.status_code}")
                    productos_con_error += 1
            
            except Exception as e:
                self.stdout.write(f"Error consultando inventario: {str(e)}")
                productos_con_error += 1
            
            # Esperar entre peticiones
            if (i + 1) % 5 == 0:
                self.stdout.write(f"Esperando 1 segundo... ({i+1}/{total_productos})")
                time.sleep(1)
        
        # Resumen final
        self.stdout.write("=== RESUMEN DE SINCRONIZACION DE INVENTARIO ===")
        self.stdout.write(f"Total productos procesados: {total_productos}")
        self.stdout.write(f"Productos con stock actualizado: {productos_actualizados}")
        self.stdout.write(f"Productos con variant_id anadido: {productos_sin_variant}")
        self.stdout.write(f"Productos con informacion de inventario: {productos_con_inventory}")
        self.stdout.write(f"Productos con error: {productos_con_error}") 