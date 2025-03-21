import requests
from django.conf import settings
from .models import Producto, TasaCambio
from decimal import Decimal
import datetime

class LoyverseService:
    BASE_URL = 'https://api.loyverse.com/v1.0'
    
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {settings.LOYVERSE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def fetch_products(self, actualizar_precios=True):
        """
        Obtiene todos los productos de Loyverse y los almacena en la base de datos local
        
        Args:
            actualizar_precios (bool): Si es True, actualiza los precios de los productos.
                                      Si hay facturas recientes (2 días), no actualiza los precios.
        """
        # Verificar si hay facturas recientes (últimos 2 días) en caso de solicitar actualización de precios
        facturas_recientes = False
        if actualizar_precios:
            from .models import Factura
            import datetime
            fecha_limite = datetime.datetime.now() - datetime.timedelta(days=2)
            facturas_recientes = Factura.objects.filter(fecha__gte=fecha_limite).exists()
            
            # Si hay facturas recientes, no actualizar precios
            if facturas_recientes:
                print(f"Se encontraron facturas recientes desde {fecha_limite}. No se actualizarán los precios.")
                actualizar_precios = False
        
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
                    
                    # Valores por defecto para todos los productos
                    defaults = {
                        'nombre': item['item_name'],
                        'descripcion': item.get('description', ''),
                        'categoria': categoria_nombre,
                        'aplicar_iva': False  # Siempre establecer aplicar_iva como False
                    }
                    
                    # Solo actualizar el precio si está habilitado y no hay facturas recientes
                    if actualizar_precios:
                        defaults.update({
                            'precio_base': precio,
                            'ultima_actualizacion_precio': updated_at,
                            'fuente_actualizacion': 'loyverse'
                        })
                    
                    # Crear o actualizar el producto
                    producto, created = Producto.objects.update_or_create(
                        loyverse_id=item['id'],
                        defaults=defaults
                    )
                    
                    if created:
                        products_created += 1
                        print(f"Nuevo producto creado: {producto.nombre} (ID: {producto.id}) - aplicar_iva=False")
                    else:
                        if not actualizar_precios:
                            prices_unchanged += 1
                        products_updated += 1
                        print(f"Producto actualizado: {producto.nombre} (ID: {producto.id}) - aplicar_iva=False")
                
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
            'facturas_recientes': facturas_recientes,
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
                        # Crear un payload más completo pero solo modificando los precios
                        update_payload = {
                            'id': data['id'],
                            'item_name': data['item_name'],
                            'description': data.get('description', ''),
                            'reference_id': data.get('reference_id'),
                            'category_id': data.get('category_id'),
                            'track_stock': data.get('track_stock', False),
                            'sold_by_weight': data.get('sold_by_weight', False),
                            'is_composite': data.get('is_composite', False),
                            'use_production': data.get('use_production', False),
                            'primary_supplier_id': data.get('primary_supplier_id'),
                            'tax_ids': data.get('tax_ids', []),
                            'form': data.get('form', 'SQUARE'),
                            'color': data.get('color', 'GREY'),
                            'option1_name': data.get('option1_name'),
                            'option2_name': data.get('option2_name'),
                            'option3_name': data.get('option3_name'),
                            'variants': []
                        }
                        
                        # Actualizar solo el precio en las variantes
                        for variant in data['variants']:
                            variant_update = {
                                'variant_id': variant['variant_id'],
                                'item_id': variant['item_id'],
                                'sku': variant.get('sku', ''),
                                'reference_variant_id': variant.get('reference_variant_id'),
                                'option1_value': variant.get('option1_value'),
                                'option2_value': variant.get('option2_value'),
                                'option3_value': variant.get('option3_value'),
                                'barcode': variant.get('barcode'),
                                'cost': variant.get('cost', 0),
                                'purchase_cost': variant.get('purchase_cost'),
                                'default_pricing_type': variant.get('default_pricing_type', 'VARIABLE'),
                                'default_price': float(product.precio_base),
                                'stores': []
                            }
                            
                            # Actualizar también el precio en cada tienda
                            if 'stores' in variant:
                                for store in variant['stores']:
                                    store_update = {
                                        'store_id': store['store_id'],
                                        'pricing_type': store.get('pricing_type', 'VARIABLE'),
                                        'price': float(product.precio_base),
                                        'available_for_sale': store.get('available_for_sale', True),
                                        'optimal_stock': store.get('optimal_stock'),
                                        'low_stock': store.get('low_stock')
                                    }
                                    variant_update['stores'].append(store_update)
                            
                            update_payload['variants'].append(variant_update)
                        
                        print(f"Actualizando precio de {product.nombre} a {float(product.precio_base)}")
                        
                        # Realizar la actualización usando PUT en lugar de POST
                        update_url = f"{self.BASE_URL}/items/{data['id']}"
                        print(f"Actualizando precio en: {update_url}")
                        
                        update_headers = self.headers.copy()
                        update_headers['Content-Type'] = 'application/json'
                        
                        update_response = requests.put(
                            update_url, 
                            headers=update_headers,
                            json=update_payload
                        )
                        
                        print(f"Status Code: {update_response.status_code}")
                        
                        if update_response.status_code in [200, 201, 204]:
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
        Calcula los precios de venta para productos basados en:
        precio_venta = (precio_compra × tasa_dolar_paralelo / unidades) × (1 + porcentaje_ganancia/100)
        
        Si se proporciona producto_id, solo calcula para ese producto.
        Si se proporciona porcentaje_ganancia, usa ese valor, de lo contrario usa el porcentaje por defecto.
        """
        try:
            # Obtener la tasa de cambio paralelo más reciente
            tasa_paralelo = TasaCambio.objects.filter(tipo='PARALELO').latest('fecha')
            
            if producto_id:
                productos = Producto.objects.filter(id=producto_id)
            else:
                productos = Producto.objects.all()
                
            for producto in productos:
                # Verificar si tenemos información de precio_compra_usd y unidades_paquete
                if producto.precio_compra_usd > 0 and producto.unidades_paquete > 0:
                    # Si no se proporciona un porcentaje específico, usar el valor por defecto (30%)
                    porcentaje = porcentaje_ganancia if porcentaje_ganancia is not None else Decimal('30.0')
                    
                    # Calcular el precio de venta según la fórmula actualizada
                    precio_base = (producto.precio_compra_usd * tasa_paralelo.valor) / Decimal(producto.unidades_paquete)
                    precio_venta = precio_base * (Decimal('1.0') + (porcentaje / Decimal('100.0')))
                    
                    # Redondear a 2 decimales
                    producto.precio_venta_calculado = round(precio_venta, 2)
                    # También actualizar el precio base para sincronizar con Loyverse
                    producto.precio_base = producto.precio_venta_calculado
                    producto.ultima_actualizacion_precio = datetime.datetime.now()
                    producto.fuente_actualizacion = 'calculado'  # Indicar que fue calculado automáticamente
                    producto.save()
                # Mantener la compatibilidad con el método anterior
                elif producto.precio_compra > 0 and producto.unidades_compra > 0:
                    # Si no se proporciona un porcentaje específico, usar el valor por defecto (30%)
                    porcentaje = porcentaje_ganancia if porcentaje_ganancia is not None else Decimal('30.0')
                    
                    # Calcular el precio de venta según la fórmula
                    precio_venta = (
                        (producto.precio_compra * tasa_paralelo.valor / Decimal(producto.unidades_compra)) *
                        (Decimal('1.0') + (porcentaje / Decimal('100.0')))
                    )
                    
                    # Redondear a 2 decimales
                    producto.precio_venta_calculado = round(precio_venta, 2)
                    # También actualizar el precio base para sincronizar con Loyverse
                    producto.precio_base = producto.precio_venta_calculado
                    producto.ultima_actualizacion_precio = datetime.datetime.now()
                    producto.fuente_actualizacion = 'calculado'  # Indicar que fue calculado automáticamente
                    producto.save()
            
            return {
                'success': True,
                'count': productos.count(),
                'message': f"Se calcularon los precios de {productos.count()} productos"
            }
            
        except TasaCambio.DoesNotExist:
            return {
                'success': False,
                'error': 'No hay tasa de cambio PARALELO registrada'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def actualizar_precios_desde_factura(self, factura_id):
        """
        Actualiza los precios de los productos basados en los datos de una factura
        y los sincroniza con Loyverse
        """
        from .models import Factura, DetalleFactura
        
        try:
            factura = Factura.objects.get(id=factura_id)
            porcentaje_global = factura.porcentaje_ganancia
            
            productos_actualizados = 0
            sync_results = []
            
            # Procesar cada detalle de la factura
            for detalle in DetalleFactura.objects.filter(factura=factura):
                producto = detalle.producto
                precio_unitario = detalle.precio_unitario  # El precio unitario introducido en la interfaz
                
                # Guardar información en el modelo de producto para referencia
                if factura.moneda == 'USD':
                    # Si la factura es en USD, guardamos directamente el precio en USD
                    producto.precio_compra_usd = detalle.precio_compra_usd
                    # Para compatibilidad con el sistema anterior
                    if factura.tasa_cambio:
                        producto.precio_compra = detalle.precio_compra_usd * factura.tasa_cambio.valor
                    else:
                        producto.precio_compra = detalle.precio_compra_usd
                else:
                    # Si la factura es en BS, convertimos a USD usando la tasa
                    if factura.tasa_cambio and factura.tasa_cambio.valor > 0:
                        producto.precio_compra_usd = detalle.precio_compra_usd
                        producto.precio_compra = detalle.precio_unitario
                
                # Guardamos la información de unidades
                producto.unidades_paquete = detalle.unidades_paquete
                producto.unidades_compra = detalle.unidades_paquete  # Para compatibilidad
                
                # Actualizar el precio base con el precio unitario de la factura
                producto.precio_base = precio_unitario
                producto.precio_venta_calculado = precio_unitario
                producto.ultima_actualizacion_precio = datetime.datetime.now()
                producto.fuente_actualizacion = 'factura'  # Registrar que fue actualizado desde factura
                producto.save()
                
                print(f"Precio actualizado para {producto.nombre}: Original: {producto.precio_base}, Nuevo: {precio_unitario}")
                
                # Sincronizar con Loyverse
                try:
                    # Obtener la información completa del producto de Loyverse
                    url = f"{self.BASE_URL}/items/{producto.loyverse_id}"
                    response = requests.get(url, headers=self.headers)
                    print(f"Consultando producto en Loyverse: {url}")
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Verificar que existan variantes
                        if 'variants' in data and len(data['variants']) > 0:
                            # Crear un payload más completo pero solo modificando los precios
                            update_payload = {
                                'id': data['id'],
                                'item_name': data['item_name'],
                                'description': data.get('description', ''),
                                'reference_id': data.get('reference_id'),
                                'category_id': data.get('category_id'),
                                'track_stock': data.get('track_stock', False),
                                'sold_by_weight': data.get('sold_by_weight', False),
                                'is_composite': data.get('is_composite', False),
                                'use_production': data.get('use_production', False),
                                'primary_supplier_id': data.get('primary_supplier_id'),
                                'tax_ids': data.get('tax_ids', []),
                                'form': data.get('form', 'SQUARE'),
                                'color': data.get('color', 'GREY'),
                                'option1_name': data.get('option1_name'),
                                'option2_name': data.get('option2_name'),
                                'option3_name': data.get('option3_name'),
                                'variants': []
                            }
                            
                            # Actualizar solo el precio en las variantes
                            for variant in data['variants']:
                                variant_update = {
                                    'variant_id': variant['variant_id'],
                                    'item_id': variant['item_id'],
                                    'sku': variant.get('sku', ''),
                                    'reference_variant_id': variant.get('reference_variant_id'),
                                    'option1_value': variant.get('option1_value'),
                                    'option2_value': variant.get('option2_value'),
                                    'option3_value': variant.get('option3_value'),
                                    'barcode': variant.get('barcode'),
                                    'cost': variant.get('cost', 0),
                                    'purchase_cost': variant.get('purchase_cost'),
                                    'default_pricing_type': variant.get('default_pricing_type', 'VARIABLE'),
                                    'default_price': float(precio_unitario),
                                    'stores': []
                                }
                                
                                # Actualizar también el precio en cada tienda
                                if 'stores' in variant:
                                    for store in variant['stores']:
                                        store_update = {
                                            'store_id': store['store_id'],
                                            'pricing_type': store.get('pricing_type', 'VARIABLE'),
                                            'price': float(precio_unitario),
                                            'available_for_sale': store.get('available_for_sale', True),
                                            'optimal_stock': store.get('optimal_stock'),
                                            'low_stock': store.get('low_stock')
                                        }
                                        variant_update['stores'].append(store_update)
                                
                                update_payload['variants'].append(variant_update)
                            
                            print(f"Actualizando precio de {producto.nombre} de {float(data['variants'][0].get('default_price', 0))} a {float(precio_unitario)}")
                            
                            # Enviar la actualización a Loyverse usando PUT
                            update_url = f"{self.BASE_URL}/items/{data['id']}"
                            print(f"Actualizando precio en: {update_url}")
                            
                            update_headers = self.headers.copy()
                            update_headers['Content-Type'] = 'application/json'
                            
                            update_response = requests.put(
                                update_url, 
                                headers=update_headers,
                                json=update_payload
                            )
                            
                            print(f"Status Code: {update_response.status_code}")
                            
                            if update_response.status_code in [200, 201, 204]:
                                productos_actualizados += 1
                                sync_results.append({
                                    "success": True,
                                    "product": producto.nombre,
                                    "price": float(precio_unitario)
                                })
                            else:
                                sync_results.append({
                                    "success": False,
                                    "product": producto.nombre,
                                    "error": update_response.text
                                })
                        else:
                            sync_results.append({
                                "success": False,
                                "product": producto.nombre,
                                "error": "No se encontraron variantes"
                            })
                    else:
                        sync_results.append({
                            "success": False,
                            "product": producto.nombre,
                            "error": f"Error obteniendo producto: {response.text}"
                        })
                except Exception as e:
                    sync_results.append({
                        "success": False,
                        "product": producto.nombre,
                        "error": str(e)
                    })
            
            # Actualizar la factura como sincronizada
            factura.sincronizado_loyverse = True
            factura.save()
            
            return {
                'success': True,
                'productos_actualizados': productos_actualizados,
                'sync_results': sync_results
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
                    # Crear un payload más completo pero solo modificando los precios
                    update_payload = {
                        'id': data['id'],
                        'item_name': data['item_name'],
                        'description': data.get('description', ''),
                        'reference_id': data.get('reference_id'),
                        'category_id': data.get('category_id'),
                        'track_stock': data.get('track_stock', False),
                        'sold_by_weight': data.get('sold_by_weight', False),
                        'is_composite': data.get('is_composite', False),
                        'use_production': data.get('use_production', False),
                        'primary_supplier_id': data.get('primary_supplier_id'),
                        'tax_ids': data.get('tax_ids', []),
                        'form': data.get('form', 'SQUARE'),
                        'color': data.get('color', 'GREY'),
                        'option1_name': data.get('option1_name'),
                        'option2_name': data.get('option2_name'),
                        'option3_name': data.get('option3_name'),
                        'variants': []
                    }
                    
                    # Actualizar solo el precio en las variantes
                    for variant in data['variants']:
                        variant_update = {
                            'variant_id': variant['variant_id'],
                            'item_id': variant['item_id'],
                            'sku': variant.get('sku', ''),
                            'reference_variant_id': variant.get('reference_variant_id'),
                            'option1_value': variant.get('option1_value'),
                            'option2_value': variant.get('option2_value'),
                            'option3_value': variant.get('option3_value'),
                            'barcode': variant.get('barcode'),
                            'cost': variant.get('cost', 0),
                            'purchase_cost': variant.get('purchase_cost'),
                            'default_pricing_type': variant.get('default_pricing_type', 'VARIABLE'),
                            'default_price': float(product.precio_base),
                            'stores': []
                        }
                        
                        # Actualizar también el precio en cada tienda
                        if 'stores' in variant:
                            for store in variant['stores']:
                                store_update = {
                                    'store_id': store['store_id'],
                                    'pricing_type': store.get('pricing_type', 'VARIABLE'),
                                    'price': float(product.precio_base),
                                    'available_for_sale': store.get('available_for_sale', True),
                                    'optimal_stock': store.get('optimal_stock'),
                                    'low_stock': store.get('low_stock')
                                }
                                variant_update['stores'].append(store_update)
                        
                        update_payload['variants'].append(variant_update)
                    
                    print(f"Actualizando precio de {product.nombre} de {float(data['variants'][0].get('default_price', 0))} a {float(product.precio_base)}")
                    
                    # Realizar la actualización usando PUT en lugar de POST
                    update_url = f"{self.BASE_URL}/items/{data['id']}"
                    print(f"Actualizando precio en: {update_url}")
                    
                    update_headers = self.headers.copy()
                    update_headers['Content-Type'] = 'application/json'
                    
                    update_response = requests.put(
                        update_url, 
                        headers=update_headers,
                        json=update_payload
                    )
                    
                    print(f"Status Code: {update_response.status_code}")
                    
                    if update_response.status_code in [200, 201, 204]:
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