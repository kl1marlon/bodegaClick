import requests
from django.conf import settings
from .models import Producto, TasaCambio
from decimal import Decimal
import datetime
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from loyverse_sync.products import aplicar_redondeo_especial
import sys  # Añadir para poder hacer flush de stdout
import re
import time

class LoyverseService:
    BASE_URL = 'https://api.loyverse.com/v1.0'
    
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def create_item(self, item_data):
        """
        Crea un nuevo producto en Loyverse
        
        Args:
            item_data (dict): Datos del producto a crear según formato de Loyverse API
            
        Returns:
            dict: Respuesta de la API si es exitosa, None si hay error
        """
        import json
        
        try:
            print(f"Creando nuevo producto en Loyverse: {item_data['item_name']}")
            
            url = f"{self.BASE_URL}/items"
            
            # Asegurar que los campos requeridos estén presentes
            required_fields = ['item_name', 'variants']
            for field in required_fields:
                if field not in item_data:
                    print(f"Error: Campo requerido '{field}' faltante en los datos del producto")
                    return None
            
            # Si no tiene category_id, establecer como None (sin categoría)
            if 'category_id' not in item_data:
                item_data['category_id'] = None
                
            # Asegurar que el precio en variants sea un número
            if 'variants' in item_data and len(item_data['variants']) > 0:
                for variant in item_data['variants']:
                    if 'default_price' in variant and variant['default_price'] is not None:
                        variant['default_price'] = float(variant['default_price'])
                    if 'cost' in variant and variant['cost'] is not None:
                        variant['cost'] = float(variant['cost'])
            
            # Realizar la petición POST
            response = requests.post(url, headers=self.headers, json=item_data)
            
            print(f"Status code: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")  # Mostrar primeros 200 caracteres para logs
            
            if response.status_code == 200 or response.status_code == 201:
                print("Producto creado exitosamente en Loyverse")
                return response.json()
            else:
                print(f"Error al crear producto en Loyverse: {response.status_code}")
                print(f"Detalles: {response.text}")
                return None
                
        except Exception as e:
            print(f"Excepción al crear producto en Loyverse: {str(e)}")
            return None
    
    def fetch_products(self, actualizar_precios=True):
        """
        Obtiene productos de Loyverse y los guarda en la base de datos local.
        
        Args:
            actualizar_precios: Si es True, actualiza los precios de productos existentes.
                                Si es False, mantiene los precios anteriores.
                                
        Returns:
            dict: Estadísticas sobre el proceso de sincronización
        """
        from .models import Producto, Factura, TasaCambio
        from django.db.models import Q
        from django.utils import timezone
        import datetime
        from datetime import timedelta
        from loyverse_sync.products import aplicar_redondeo_especial
        
        # Obtener las categorías para mapear IDs a nombres
        categories_dict = {}
        try:
            print("Obteniendo categorías desde Loyverse...")
            categories_response = requests.get(f"{self.BASE_URL}/categories", headers=self.headers)
            if categories_response.status_code == 200:
                categories_data = categories_response.json()
                categories = categories_data.get('categories', [])
                
                for category in categories:
                    category_id = category.get('id')
                    category_name = category.get('name')
                    if category_id and category_name:
                        categories_dict[category_id] = category_name
                print(f"Se encontraron {len(categories_dict)} categorías en Loyverse")
            else:
                print(f"Error al obtener categorías: {categories_response.status_code} - {categories_response.text}")
        except Exception as e:
            print(f"Error obteniendo categorías: {str(e)}")
        
        # Inicializar contadores
        products_created = 0
        products_updated = 0
        prices_unchanged = 0
        total_items_processed = 0
        
        # Inicializar cursor para paginación
        cursor = None
        page = 1
        
        print(f"Iniciando sincronización de productos con paginación. Actualizar precios: {actualizar_precios}")
        
        while True:
            # Construir URL con cursor si existe
            url = f"{self.BASE_URL}/items"
            if cursor:
                url += f"?cursor={cursor}"
            
            print(f"Procesando página {page}, URL: {url}")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Error en la API de Loyverse: {response.status_code} - {response.text}")
                if page == 1:  # Si falla en la primera página, devolver error
                    return {
                        'success': False,
                        'error': f'Error al obtener productos: {response.status_code} - {response.text}'
                    }
                else:  # Si falla después de la primera página, devolver los resultados parciales
                    break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                print(f"No hay más productos para procesar. Total procesados: {total_items_processed}")
                break
            
            print(f"Procesando {len(items)} productos en la página {page}")
            total_items_processed += len(items)
            
            for item in items:
                try:
                    # Tomamos el primer variante como precio base
                    precio = Decimal('0')
                    if item.get('variants'):
                        variant = item['variants'][0]
                        precio_str = str(variant.get('default_price', '0'))
                        # Asegurarse de que el precio sea un número válido
                        try:
                            precio = Decimal(precio_str)
                        except:
                            print(f"Precio inválido para {item['item_name']}: {precio_str}")
                            precio = Decimal('0')
                    
                    # Obtener el ID de categoría y mapear al nombre
                    categoria_id = item.get('category_id', '')
                    categoria_nombre = categories_dict.get(categoria_id, '')
                    
                    # Convertir la fecha de actualización de Loyverse a formato datetime
                    updated_at = None
                    if item.get('updated_at'):
                        try:
                            updated_at = datetime.datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
                        except Exception as e:
                            print(f"Error al convertir fecha: {str(e)}")
                    
                    # Buscar si el producto ya existe para decidir si actualizar el precio
                    try:
                        producto_existente = Producto.objects.get(loyverse_id=item['id'])
                        defaults = {
                            'nombre': item['item_name'],
                            'descripcion': item.get('description', ''),
                            'categoria': categoria_nombre,
                            'aplicar_iva': False  # Establecer aplicar_iva como False por defecto para productos de Loyverse
                        }
                        
                        # Guardar el variant_id si está disponible
                        if item.get('variants') and len(item['variants']) > 0:
                            variant_id = item['variants'][0].get('variant_id')
                            if variant_id:
                                defaults['variant_id'] = variant_id
                        
                        # Solo actualizar el precio si está habilitado y no hay facturas recientes
                        if actualizar_precios:
                            # Aplicar redondeo especial si es necesario
                            precio_redondeado = aplicar_redondeo_especial(precio)
                            defaults.update({
                                'precio_base': precio_redondeado,
                                'ultima_actualizacion_precio': updated_at,
                                'fuente_actualizacion': 'loyverse'
                            })
                            print(f"Aplicando precio redondeado para {item['item_name']}: {precio} -> {precio_redondeado}")
                        else:
                            prices_unchanged += 1
                        
                        # Actualizar el producto con los valores correspondientes
                        for key, value in defaults.items():
                            setattr(producto_existente, key, value)
                        
                        # Asegurar que aplicar_iva siempre sea False para productos sincronizados
                        producto_existente.aplicar_iva = False
                        
                        producto_existente.save()
                        print(f"Producto actualizado: {producto_existente.nombre} (ID: {producto_existente.id}) - aplicar_iva={producto_existente.aplicar_iva}")
                        products_updated += 1
                        
                    except Producto.DoesNotExist:
                        # Para productos nuevos, siempre establecer todos los valores
                        variant_id = None
                        if item.get('variants') and len(item['variants']) > 0:
                            variant_id = item['variants'][0].get('variant_id')
                            
                        nuevo_producto = Producto.objects.create(
                            loyverse_id=item['id'],
                            variant_id=variant_id,
                            nombre=item['item_name'],
                            descripcion=item.get('description', ''),
                            precio_base=precio,
                            categoria=categoria_nombre,
                            ultima_actualizacion_precio=updated_at,
                            fuente_actualizacion='loyverse',
                            aplicar_iva=False  # Establecer aplicar_iva como False por defecto para productos de Loyverse
                        )
                        print(f"Nuevo producto creado: {nuevo_producto.nombre} (ID: {nuevo_producto.id}) - aplicar_iva={nuevo_producto.aplicar_iva}")
                        products_created += 1
                
                except Exception as e:
                    print(f"Error procesando producto {item.get('item_name', 'desconocido')}: {str(e)}")
                    continue
            
            # Obtener el cursor para la siguiente página
            cursor = data.get('cursor')
            if not cursor:
                print("No hay más páginas para procesar (cursor es None)")
                break
            
            page += 1
            print(f"Pasando a la página {page} con cursor: {cursor}")
        
        print(f"Sincronización completada. Creados: {products_created}, Actualizados: {products_updated}, Precios no modificados: {prices_unchanged}")
        return {
            'success': True,
            'created': products_created,
            'updated': products_updated,
            'prices_unchanged': prices_unchanged,
            'total_pages': page,
            'total_processed': total_items_processed
        }

    def sync_prices(self, products):
        """
        Sincroniza los precios de los productos con Loyverse
        """
        updated_count = 0
        failed_count = 0
        
        for product in products:
            try:
                # Primero obtener la información completa del producto
                url = f"{self.BASE_URL}/items/{product.loyverse_id}"
                response = requests.get(url, headers=self.headers)
                print(f"Consultando producto en Loyverse: {url}")
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar que existan variantes
                    if 'variants' in data and len(data['variants']) > 0:
                        # Obtener todos los datos del producto para mantener la información existente
                        update_payload = data.copy()
                        
                        # Actualizar el precio en todas las variantes
                        for variant in update_payload['variants']:
                            variant['default_price'] = float(product.precio_base)
                            
                            # Actualizar también el precio en cada tienda
                            if 'stores' in variant:
                                for store in variant['stores']:
                                    store['price'] = float(product.precio_base)
                        
                        print("Payload para actualización:")
                        print(update_payload)
                        
                        # Realizar la actualización usando POST en el endpoint de items
                        update_url = f"{self.BASE_URL}/items"
                        print(f"Actualizando precio en: {update_url}")
                        
                        update_headers = self.headers.copy()
                        update_headers['Content-Type'] = 'application/json'
                        
                        update_response = requests.post(
                            update_url, 
                            headers=update_headers,
                            json=update_payload
                        )
                        
                        print(f"Status Code: {update_response.status_code}")
                        
                        if update_response.status_code == 200:
                            updated_count += 1
                            print(f"Producto actualizado exitosamente: {product.nombre}")
                        else:
                            failed_count += 1
                            print(f"Error actualizando {product.nombre}: {update_response.text}")
                    else:
                        failed_count += 1
                        print(f"No se encontraron variantes para el producto {product.nombre}")
                else:
                    failed_count += 1
                    print(f"Error obteniendo producto {product.nombre}: {response.text}")
            
            except Exception as e:
                failed_count += 1
                print(f"Error procesando {product.nombre}: {str(e)}")
        
        return {
            'success': updated_count > 0,
            'updated': updated_count,
            'failed': failed_count
        }
        
    def calcular_precios_venta(self, producto_id=None, porcentaje_ganancia=None):
        """
        Calcula los precios de venta para productos, basado en el precio de compra, 
        unidades por paquete y un porcentaje de ganancia.
        Utiliza la tasa de cambio paralelo más reciente.
        
        Args:
            producto_id: ID específico de un producto (opcional)
            porcentaje_ganancia: Porcentaje de ganancia a aplicar (opcional, default: 30%)
            
        Returns:
            dict: Resultados de la operación
        """
        # Importar aquí para evitar problemas de importación circular
        from loyverse_sync.products import aplicar_redondeo_especial
        from decimal import Decimal
        import datetime
        from facturacion.models import Producto, TasaCambio
        
        # Obtener la última tasa paralelo
        try:
            tasa_paralelo = TasaCambio.objects.filter(tipo='PARALELO').latest('fecha')
        except TasaCambio.DoesNotExist:
            return {'success': False, 'error': 'No hay tasa PARALELO disponible'}
        
        # Filtrar productos si se especifica un ID
        if producto_id:
            productos = Producto.objects.filter(id=producto_id)
        else:
            productos = Producto.objects.all()
            
        productos_actualizados = 0
            
        for producto in productos:
            # Verificar si tenemos información de precio_compra_usd y unidades_paquete
            if producto.precio_compra_usd > 0 and producto.unidades_paquete > 0:
                # Si no se proporciona un porcentaje específico, usar el valor por defecto (30%)
                porcentaje = porcentaje_ganancia if porcentaje_ganancia is not None else Decimal('30.0')
                
                # Calcular el precio de venta según la fórmula actualizada
                precio_base = (producto.precio_compra_usd * tasa_paralelo.valor) / Decimal(producto.unidades_paquete)
                precio_venta = precio_base * (Decimal('1.0') + (porcentaje / Decimal('100.0')))
                
                # Redondear a 2 decimales primero para evitar problemas de precisión
                precio_venta_redondeado = round(precio_venta, 2)
                
                # Aplicar reglas de redondeo especiales para precios en bolívares
                precio_final = aplicar_redondeo_especial(precio_venta_redondeado)
                
                # Actualizar los campos del producto
                producto.precio_venta_calculado = precio_final
                # También actualizar el precio base para sincronizar con Loyverse
                producto.precio_base = precio_final
                producto.ultima_actualizacion_precio = datetime.datetime.now()
                producto.fuente_actualizacion = 'calculado'  # Indicar que fue calculado automáticamente
                producto.save()
                
                productos_actualizados += 1
                
        return {
            'success': True,
            'actualizados': productos_actualizados,
            'total_productos': len(productos)
        }
    
    def actualizar_precios_desde_factura(self, factura_id):
        """
        Actualiza los precios de los productos basados en los datos de una factura
        y los sincroniza con Loyverse
        """
        from .models import Factura, DetalleFactura
        from loyverse_sync.products import aplicar_redondeo_especial
        
        try:
            factura = Factura.objects.get(id=factura_id)
            porcentaje_global = factura.porcentaje_ganancia
            
            productos_actualizados = 0
            sync_results = []
            
            # ID específico de la tienda principal de Loyverse
            # NOTA: Esto debe cambiarse si se usa en otra tienda
            store_id = '8aa31f38-96ee-4887-ad51-0362dfa034e6'
            print(f"Usando tienda con ID: {store_id}")
            
            # Lista para almacenar los cambios de inventario
            inventory_updates = []
            
            # Procesar cada detalle de la factura
            detalles = DetalleFactura.objects.filter(factura=factura)
            print(f"Procesando {detalles.count()} productos en la factura")
            
            for detalle in detalles:
                producto = detalle.producto
                print(f"Procesando producto: {producto.nombre} (ID Loyverse: {producto.loyverse_id})")
                
                # Verificar que el producto tenga ID de Loyverse
                if not producto.loyverse_id:
                    print(f"Producto {producto.nombre} no tiene ID de Loyverse")
                    sync_results.append({
                        "success": False,
                        "product": producto.nombre,
                        "error": "El producto no tiene ID de Loyverse"
                    })
                    continue
                
                # Usar variant_id si está disponible, de lo contrario obtenerlo
                variant_id = None
                if producto.variant_id:
                    variant_id = producto.variant_id
                    print(f"Usando variant_id almacenado: {variant_id}")
                else:
                    # Obtener variant_id desde la API de Loyverse
                    try:
                        # Obtener datos del producto para encontrar el ID de la variante correcta
                        item_url = f"{self.BASE_URL}/items/{producto.loyverse_id}"
                        print(f"Obteniendo datos del producto en: {item_url}")
                        item_response = requests.get(item_url, headers=self.headers)
                        
                        if item_response.status_code != 200:
                            print(f"Error al obtener datos del producto: {item_response.text}")
                            sync_results.append({
                                "success": False,
                                "product": producto.nombre,
                                "error": f"Error obteniendo datos del producto: {item_response.text}"
                            })
                            continue
                        
                        # Obtener el ID de la primera variante (generalmente hay solo una)
                        item_data = item_response.json()
                        if not item_data.get('variants') or len(item_data['variants']) == 0:
                            print(f"No se encontraron variantes para el producto {producto.nombre}")
                            sync_results.append({
                                "success": False,
                                "product": producto.nombre,
                                "error": "No se encontraron variantes para el producto"
                            })
                            continue
                        
                        # Obtener el ID de la variante y guardarlo para futuras consultas
                        variant_id = item_data['variants'][0]['variant_id']
                        producto.variant_id = variant_id
                        producto.save(update_fields=['variant_id'])
                        print(f"ID de variante encontrado y guardado: {variant_id}")
                    except Exception as e:
                        print(f"Error al obtener variant_id: {str(e)}")
                        sync_results.append({
                            "success": False,
                            "product": producto.nombre,
                            "error": f"Error al obtener variant_id: {str(e)}"
                        })
                        continue
                
                # Consultar el inventario actual
                try:
                    inventory_url = f"{self.BASE_URL}/inventory?variant_ids={variant_id}"
                    print(f"Consultando inventario en: {inventory_url}")
                    inventory_response = requests.get(inventory_url, headers=self.headers)
                    print(f"Respuesta de inventario: {inventory_response.status_code}")
                    
                    if inventory_response.status_code == 200:
                        inventory_data = inventory_response.json()
                        inventory_levels = inventory_data.get('inventory_levels', [])
                        print(f"Niveles de inventario recibidos: {len(inventory_levels)}")
                        
                        # Buscar el nivel de inventario para la tienda principal
                        current_stock = 0
                        for level in inventory_levels:
                            if level.get('store_id') == store_id and level.get('variant_id') == variant_id:
                                current_stock = level.get('in_stock', 0)
                                print(f"Stock actual en Loyverse: {current_stock}")
                                break
                        
                        # Calcular el nuevo stock sumando las unidades del detalle
                        cantidad = float(detalle.cantidad if detalle.cantidad else 0)
                        unidades = float(detalle.unidades_paquete if detalle.unidades_paquete else 1)
                        
                        cantidad_unidades = cantidad * unidades
                        print(f"Cantidad: {cantidad}, Unidades por paquete: {unidades}")
                        nuevo_stock = current_stock + cantidad_unidades
                        print(f"Añadiendo {cantidad_unidades} unidades para un nuevo stock de: {nuevo_stock}")
                        
                        # Agregar a la lista de actualizaciones utilizando el ID de la VARIANTE
                        inventory_updates.append({
                            "variant_id": variant_id,
                            "store_id": store_id,
                            "stock_after": nuevo_stock
                        })
                        
                        sync_results.append({
                            "success": True,
                            "product": producto.nombre,
                            "current_stock": current_stock,
                            "added_units": cantidad_unidades,
                            "new_stock": nuevo_stock,
                            "variant_id": variant_id
                        })
                    else:
                        print(f"Error al consultar inventario: {inventory_response.text}")
                        sync_results.append({
                            "success": False,
                            "product": producto.nombre,
                            "error": f"Error consultando inventario: {inventory_response.text}"
                        })
                except Exception as e:
                    print(f"Error al consultar inventario: {str(e)}")
                    sync_results.append({
                        "success": False,
                        "product": producto.nombre,
                        "error": str(e)
                    })
            
            # Realizar la actualización de inventario en Loyverse
            update_url = f"{self.BASE_URL}/inventory"
            print(f"Enviando actualización de inventario a Loyverse con {len(inventory_updates)} productos")
            print(f"Payload de actualización: {inventory_updates}")
            
            # Lista para almacenar los IDs de elementos que fallaron por track_stock: false
            failed_items = []
            retry_count = 0
            max_retries = 3  # Número máximo de reintentos
            
            while retry_count <= max_retries and inventory_updates:
                try:
                    update_payload = {'inventory_levels': inventory_updates}
                    update_response = requests.post(update_url, headers=self.headers, json=update_payload)
                    print(f"Respuesta de actualización de inventario: {update_response.status_code}")
                    
                    # Si la actualización fue exitosa, salimos del bucle
                    if update_response.status_code == 200:
                        print("Inventario actualizado correctamente en Loyverse")
                        return {
                            'success': True,
                            'message': 'Inventory updated successfully',
                            'productos_actualizados': len(inventory_updates),
                            'productos_omitidos': failed_items,
                            'resultados_detalle': sync_results
                        }
                    
                    # Si hay un error, analizamos la respuesta para identificar el elemento problemático
                    error_data = update_response.json()
                    print(f"Error al actualizar inventario: {error_data}")
                    
                    # Verificar si el error es por track_stock: false
                    problem_id = None
                    reason = None
                    if 'errors' in error_data and len(error_data['errors']) > 0:
                        for error in error_data['errors']:
                            details = error.get('details', '')
                            is_track_stock_error = 'track_stock' in details and 'false' in details
                            is_use_production_error = 'use_production' in details and 'false' in details
                            
                            if is_track_stock_error or is_use_production_error:
                                # Extraer el ID del elemento problemático
                                import re
                                match = re.search(r"id '([^']+)'", details)
                                if match:
                                    problem_id = match.group(1)
                                    reason = 'track_stock: false' if is_track_stock_error else 'use_production: false'
                                    print(f"Identificado elemento problemático con ID: {problem_id}, Razón: {reason}")
                                    
                                    # Filtrar el elemento problemático de la lista de actualizaciones
                                    filtered_updates = []
                                    item_found_for_removal = False
                                    for item in inventory_updates:
                                        if item['variant_id'] == problem_id:
                                            failed_items.append({
                                                'variant_id': item['variant_id'],
                                                'reason': reason
                                            })
                                            item_found_for_removal = True
                                        else:
                                            filtered_updates.append(item)
                                    
                                    # Si el item no se encontró (esto no debería pasar pero por seguridad)
                                    if not item_found_for_removal:
                                         print(f"No se encontró el item {problem_id} en la lista para filtrar, deteniendo reintentos.")
                                         return {
                                            'success': False,
                                            'error': f"Error interno: No se pudo filtrar el item {problem_id}",
                                            'productos_omitidos': failed_items,
                                            'resultados_detalle': sync_results
                                        }
                                    
                                    # Actualizar la lista para el siguiente intento
                                    inventory_updates = filtered_updates
                                    print(f"Reintentando con {len(inventory_updates)} elementos después de filtrar")
                                    
                                    # Si no quedan elementos para actualizar, salimos
                                    if not inventory_updates:
                                        print("No quedan elementos válidos para actualizar")
                                        return {
                                            'success': True,
                                            'message': 'Partial inventory update',
                                            'productos_actualizados': 0,
                                            'productos_omitidos': failed_items,
                                            'resultados_detalle': sync_results
                                        }
                                    
                                    # Incrementar contador de reintentos y continuar el bucle while
                                    retry_count += 1
                                    break # Salir del bucle de errores una vez identificado
                                
                    # Si no pudimos identificar el elemento problemático o no es por track_stock
                    if retry_count == 0 or len(inventory_updates) == len(update_payload['inventory_levels']):
                        return {
                            'success': False,
                            'error': f"Error al actualizar inventario: {error_data}",
                            'productos_omitidos': failed_items,
                            'resultados_detalle': sync_results
                        }
                
                except Exception as e:
                    print(f"Excepción durante la actualización de inventario: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error inesperado durante actualización: {str(e)}",
                        'productos_omitidos': failed_items,
                        'resultados_detalle': sync_results
                    }
            
            # Si llegamos aquí, es porque agotamos los reintentos
            return {
                'success': len(failed_items) < len(inventory_updates) + len(failed_items),
                'message': f"Actualización parcial después de {retry_count} reintentos",
                'productos_actualizados': len(inventory_updates),
                'productos_omitidos': failed_items,
                'resultados_detalle': sync_results
            }

        except Factura.DoesNotExist:
            return {
                'success': False,
                'error': f'No se encontró la factura con ID {factura_id}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def sync_single_product(self, product):
        """
        Sincroniza un solo producto con Loyverse
        """
        try:
            # Primero obtener la información completa del producto
            url = f"{self.BASE_URL}/items/{product.loyverse_id}"
            response = requests.get(url, headers=self.headers)
            print(f"Consultando producto en Loyverse: {url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que existan variantes
                if 'variants' in data and len(data['variants']) > 0:
                    # Obtener todos los datos del producto para mantener la información existente
                    update_payload = data.copy()
                    
                    # Actualizar el precio en todas las variantes
                    for variant in update_payload['variants']:
                        print(f"Actualizando precio de {product.nombre} de {variant['default_price']} a {float(product.precio_base)}")
                        variant['default_price'] = float(product.precio_base)
                        
                        # Actualizar también el precio en cada tienda
                        if 'stores' in variant:
                            for store in variant['stores']:
                                store['price'] = float(product.precio_base)
                    
                    print("Payload para actualización:")
                    print(update_payload)
                    
                    # Realizar la actualización usando POST en el endpoint de items
                    update_url = f"{self.BASE_URL}/items"
                    print(f"Actualizando precio en: {update_url}")
                    
                    update_headers = self.headers.copy()
                    update_headers['Content-Type'] = 'application/json'
                    
                    update_response = requests.post(
                        update_url, 
                        headers=update_headers,
                        json=update_payload
                    )
                    
                    print(f"Status Code: {update_response.status_code}")
                    
                    if update_response.status_code == 200:
                        return {
                            "success": True,
                            "product": product.nombre,
                            "price": float(product.precio_base)
                        }
                    else:
                        return {
                            "success": False,
                            "product": product.nombre,
                            "error": update_response.text
                        }
                else:
                    return {
                        "success": False,
                        "product": product.nombre,
                        "error": "No se encontraron variantes"
                    }
            else:
                return {
                    "success": False,
                    "product": product.nombre,
                    "error": f"Error obteniendo producto: {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "product": product.nombre,
                "error": str(e)
            }

    def test_webhook(self, webhook):
        """
        Envía una solicitud de prueba a un webhook
        """
        try:
            # Crear datos de prueba según el tipo de webhook
            test_data = self._generate_test_data(webhook.type)
            
            # Enviar solicitud de prueba al webhook
            response = requests.post(
                webhook.url,
                json=test_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-Loyverse-API-version': 'v1.0',
                    # No incluimos firma para pruebas
                }
            )
            
            return {
                'success': 200 <= response.status_code < 300,
                'status_code': response.status_code,
                'response': response.text,
                'test_data': test_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_test_data(self, webhook_type):
        """
        Genera datos de prueba según el tipo de webhook
        """
        import uuid
        from datetime import datetime
        
        # ID de prueba
        test_id = str(uuid.uuid4())
        
        # Timestamp actual
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Datos comunes
        common_data = {
            'merchant_id': 'test-merchant-id',
            'type': webhook_type,
            'created_at': now
        }
        
        # Generar datos específicos según el tipo
        if webhook_type == 'inventory_levels.update':
            return {
                **common_data,
                'inventory_levels': [
                    {
                        'variant_id': test_id,
                        'store_id': test_id,
                        'in_stock': 10,
                        'updated_at': now
                    }
                ]
            }
        elif webhook_type == 'orders.update':
            return {
                **common_data,
                'orders': [
                    {
                        'order_id': test_id,
                        'store_id': test_id,
                        'updated_at': now,
                        'status': 'COMPLETED'
                    }
                ]
            }
        else:
            # Para otros tipos, usar datos genéricos
            return common_data
    
    def create_webhook(self, url, webhook_type):
        """
        Crea un nuevo webhook en Loyverse
        """
        webhook_url = f"{self.BASE_URL}/webhooks"
        payload = {
            'url': url,
            'type': webhook_type
        }
        
        response = requests.post(webhook_url, json=payload, headers=self.headers)
        
        if response.status_code == 200:
            return {
                'success': True,
                'webhook': response.json()
            }
        
        return {
            'success': False,
            'error': f'Error al crear webhook: {response.status_code}'
        }
    
    def list_webhooks(self):
        """
        Lista todos los webhooks configurados en Loyverse
        """
        webhook_url = f"{self.BASE_URL}/webhooks"
        response = requests.get(webhook_url, headers=self.headers)
        
        if response.status_code == 200:
            return {
                'success': True,
                'webhooks': response.json().get('webhooks', [])
            }
        
        return {
            'success': False,
            'error': f'Error al listar webhooks: {response.status_code}'
        }
    
    def delete_webhook(self, webhook_id):
        """
        Elimina un webhook en Loyverse
        """
        webhook_url = f"{self.BASE_URL}/webhooks/{webhook_id}"
        response = requests.delete(webhook_url, headers=self.headers)
        
        if response.status_code == 204:
            return {
                'success': True
            }
        
        return {
            'success': False,
            'error': f'Error al eliminar webhook: {response.status_code}'
        }

    def actualizar_inventario_desde_factura(self, factura_id):
        """
        Actualiza el inventario en Loyverse basado en los productos de una factura,
        sumando las unidades nuevas al inventario existente.
        """
        from .models import Factura, DetalleFactura, Producto
        import datetime
        import sys
        
        print(f"INICIANDO actualizar_inventario_desde_factura para factura ID: {factura_id}")
        sys.stdout.flush()
        
        try:
            factura = Factura.objects.get(id=factura_id)
            productos_actualizados = 0
            update_results = []
            
            # ID específico de la tienda principal de Loyverse
            # NOTA: Esto debe cambiarse si se usa en otra tienda
            store_id = '8aa31f38-96ee-4887-ad51-0362dfa034e6'
            print(f"Usando tienda con ID: {store_id}")
            sys.stdout.flush()
            
            # Lista para almacenar los cambios de inventario
            inventory_updates = []
            
            # Procesar cada detalle de la factura
            detalles = DetalleFactura.objects.filter(factura=factura)
            print(f"Procesando {detalles.count()} productos en la factura")
            sys.stdout.flush()
            
            for detalle in detalles:
                producto = detalle.producto
                print(f"Procesando producto: {producto.nombre} (ID Loyverse: {producto.loyverse_id})")
                sys.stdout.flush()
                
                # Verificar que el producto tenga ID de Loyverse
                if not producto.loyverse_id:
                    print(f"Producto {producto.nombre} no tiene ID de Loyverse")
                    update_results.append({
                        "success": False,
                        "product": producto.nombre,
                        "error": "El producto no tiene ID de Loyverse"
                    })
                    continue
                
                # Usar variant_id si está disponible, de lo contrario obtenerlo
                variant_id = None
                if producto.variant_id:
                    variant_id = producto.variant_id
                    print(f"Usando variant_id almacenado: {variant_id}")
                else:
                    # Obtener variant_id desde la API de Loyverse
                    try:
                        # Obtener datos del producto para encontrar el ID de la variante correcta
                        item_url = f"{self.BASE_URL}/items/{producto.loyverse_id}"
                        print(f"Obteniendo datos del producto en: {item_url}")
                        sys.stdout.flush()
                        item_response = requests.get(item_url, headers=self.headers)
                        
                        if item_response.status_code != 200:
                            print(f"Error al obtener datos del producto: {item_response.text}")
                            sys.stdout.flush()
                            update_results.append({
                                "success": False,
                                "product": producto.nombre,
                                "error": f"Error obteniendo datos del producto: {item_response.text}"
                            })
                            continue
                        
                        # Obtener el ID de la primera variante (generalmente hay solo una)
                        item_data = item_response.json()
                        if not item_data.get('variants') or len(item_data['variants']) == 0:
                            print(f"No se encontraron variantes para el producto {producto.nombre}")
                            sys.stdout.flush()
                            update_results.append({
                                "success": False,
                                "product": producto.nombre,
                                "error": "No se encontraron variantes para el producto"
                            })
                            continue
                        
                        # Obtener el ID de la variante y guardarlo para futuras consultas
                        variant_id = item_data['variants'][0]['variant_id']
                        producto.variant_id = variant_id
                        producto.save(update_fields=['variant_id'])
                        print(f"ID de variante encontrado y guardado: {variant_id}")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"Error al obtener variant_id: {str(e)}")
                        update_results.append({
                            "success": False,
                            "product": producto.nombre,
                            "error": f"Error al obtener variant_id: {str(e)}"
                        })
                        continue
                
                # Consultar el inventario actual
                try:
                    inventory_url = f"{self.BASE_URL}/inventory?variant_ids={variant_id}"
                    print(f"Consultando inventario en: {inventory_url}")
                    sys.stdout.flush()
                    inventory_response = requests.get(inventory_url, headers=self.headers)
                    print(f"Respuesta de inventario: {inventory_response.status_code}")
                    sys.stdout.flush()
                    
                    if inventory_response.status_code == 200:
                        inventory_data = inventory_response.json()
                        inventory_levels = inventory_data.get('inventory_levels', [])
                        print(f"Niveles de inventario recibidos: {len(inventory_levels)}")
                        sys.stdout.flush()
                        
                        # Buscar el nivel de inventario para la tienda principal
                        current_stock = 0
                        for level in inventory_levels:
                            if level.get('store_id') == store_id and level.get('variant_id') == variant_id:
                                current_stock = level.get('in_stock', 0)
                                print(f"Stock actual en Loyverse: {current_stock}")
                                sys.stdout.flush()
                                break
                        
                        # Calcular el nuevo stock sumando las unidades del detalle
                        cantidad = float(detalle.cantidad if detalle.cantidad else 0)
                        unidades = float(detalle.unidades_paquete if detalle.unidades_paquete else 1)
                        
                        cantidad_unidades = cantidad * unidades
                        print(f"Cantidad: {cantidad}, Unidades por paquete: {unidades}")
                        sys.stdout.flush()
                        nuevo_stock = current_stock + cantidad_unidades
                        print(f"Añadiendo {cantidad_unidades} unidades para un nuevo stock de: {nuevo_stock}")
                        sys.stdout.flush()
                        
                        # Agregar a la lista de actualizaciones utilizando el ID de la VARIANTE
                        inventory_updates.append({
                            "variant_id": variant_id,
                            "store_id": store_id,
                            "stock_after": nuevo_stock
                        })
                        
                        update_results.append({
                            "success": True,
                            "product": producto.nombre,
                            "current_stock": current_stock,
                            "added_units": cantidad_unidades,
                            "new_stock": nuevo_stock,
                            "variant_id": variant_id
                        })
                    else:
                        print(f"Error al consultar inventario: {inventory_response.text}")
                        update_results.append({
                            "success": False,
                            "product": producto.nombre,
                            "error": f"Error consultando inventario: {inventory_response.text}"
                        })
                except Exception as e:
                    print(f"Error al consultar inventario: {str(e)}")
                    update_results.append({
                        "success": False,
                        "product": producto.nombre,
                        "error": str(e)
                    })
            
            # Realizar la actualización de inventario en Loyverse
            update_url = f"{self.BASE_URL}/inventory"
            print(f"Enviando actualización de inventario a Loyverse con {len(inventory_updates)} productos")
            print(f"Payload de actualización: {inventory_updates}")
            sys.stdout.flush()
            
            # Lista para almacenar los IDs de elementos que fallaron por track_stock: false
            failed_items = []
            retry_count = 0
            max_retries = 3  # Número máximo de reintentos
            
            while retry_count <= max_retries and inventory_updates:
                try:
                    update_payload = {'inventory_levels': inventory_updates}
                    update_response = requests.post(update_url, headers=self.headers, json=update_payload)
                    print(f"Respuesta de actualización de inventario: {update_response.status_code}")
                    sys.stdout.flush()
                    
                    # Si la actualización fue exitosa, salimos del bucle
                    if update_response.status_code == 200:
                        print("Inventario actualizado correctamente en Loyverse")
                        sys.stdout.flush()
                        return {
                            'success': True,
                            'message': 'Inventory updated successfully',
                            'productos_actualizados': len(inventory_updates),
                            'productos_omitidos': failed_items,
                            'resultados_detalle': update_results
                        }
                    
                    # Si hay un error, analizamos la respuesta para identificar el elemento problemático
                    error_data = update_response.json()
                    print(f"Error al actualizar inventario: {error_data}")
                    sys.stdout.flush()
                    
                    # Verificar si el error es por track_stock: false o use_production: false
                    problem_id = None
                    reason = None
                    if 'errors' in error_data and len(error_data['errors']) > 0:
                        for error in error_data['errors']:
                            details = error.get('details', '')
                            is_track_stock_error = 'track_stock' in details and 'false' in details
                            is_use_production_error = 'use_production' in details and 'false' in details
                            
                            if is_track_stock_error or is_use_production_error:
                                # Extraer el índice del producto problemático desde el campo 'field' del error de Loyverse
                                import re
                                index_match = re.search(r'inventory_levels\[(\d+)\]', error.get('field', ''))
                                if index_match:
                                    problematic_index = int(index_match.group(1))
                                    reason = 'track_stock: false' if is_track_stock_error else 'use_production: false'
                                    print(f"Identificado elemento problemático en índice: {problematic_index}, Razón: {reason}")
                                    sys.stdout.flush()
                                    
                                    # Filtrar el elemento problemático de la lista de actualizaciones
                                    filtered_updates = []
                                    item_found_for_removal = False
                                    for i, item in enumerate(inventory_updates):
                                        if i == problematic_index:
                                            failed_items.append({
                                                'variant_id': item['variant_id'],
                                                'reason': reason
                                            })
                                            item_found_for_removal = True
                                        else:
                                            filtered_updates.append(item)
                                    
                                    # Si el item no se encontró (esto no debería pasar pero por seguridad)
                                    if not item_found_for_removal:
                                         print(f"No se encontró el item en el índice {problematic_index} en la lista para filtrar, deteniendo reintentos.")
                                         return {
                                            'success': False,
                                            'error': f"Error interno: No se pudo filtrar el item en el índice {problematic_index}",
                                            'productos_omitidos': failed_items,
                                            'resultados_detalle': update_results
                                        }
                                    
                                    # Actualizar la lista para el siguiente intento
                                    inventory_updates = filtered_updates
                                    print(f"Reintentando con {len(inventory_updates)} elementos después de filtrar")
                                    sys.stdout.flush()
                                    
                                    # Si no quedan elementos para actualizar, salimos
                                    if not inventory_updates:
                                        print("No quedan elementos válidos para actualizar")
                                        sys.stdout.flush()
                                        return {
                                            'success': True,
                                            'message': 'Partial inventory update',
                                            'productos_actualizados': 0,
                                            'productos_omitidos': failed_items,
                                            'resultados_detalle': update_results
                                        }
                                    
                                    # Incrementar contador de reintentos y continuar el bucle while
                                    retry_count += 1
                                    break # Volver al inicio del while para reintentar
                                
                    # Si no pudimos identificar el elemento problemático o no es por track_stock
                    if retry_count == 0 or len(inventory_updates) == len(update_payload['inventory_levels']):
                        return {
                            'success': False,
                            'error': f"Error al actualizar inventario: {error_data}",
                            'productos_omitidos': failed_items,
                            'resultados_detalle': update_results
                        }
                
                except Exception as e:
                    print(f"Excepción durante la actualización de inventario: {str(e)}")
                    sys.stdout.flush()
                    return {
                        'success': False,
                        'error': f"Error inesperado durante actualización: {str(e)}",
                        'productos_omitidos': failed_items,
                        'resultados_detalle': update_results
                    }
            
            # Si llegamos aquí, es porque agotamos los reintentos
            return {
                'success': len(failed_items) < len(inventory_updates) + len(failed_items),
                'message': f"Actualización parcial después de {retry_count} reintentos",
                'productos_actualizados': len(inventory_updates),
                'productos_omitidos': failed_items,
                'resultados_detalle': update_results
            }

        except Factura.DoesNotExist:
            print(f"No se encontró la factura con ID {factura_id}")
            sys.stdout.flush()
            return {
                'success': False,
                'error': f'No se encontró la factura con ID {factura_id}'
            }
        except Exception as e:
            print(f"Error general: {str(e)}")
            sys.stdout.flush()
            return {
                'success': False,
                'error': str(e)
            } 