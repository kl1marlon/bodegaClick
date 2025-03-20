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
                            # Crear una copia para mantener toda la información
                            update_payload = data.copy()
                            
                            # Actualizar SOLO el precio en todas las variantes con el precio_unitario
                            for variant in update_payload['variants']:
                                print(f"Actualizando precio de {producto.nombre} de {variant['default_price']} a {float(precio_unitario)}")
                                
                                # Usar directamente el precio_unitario de la factura
                                variant['default_price'] = float(precio_unitario)
                                
                                # Actualizar también en las tiendas
                                if 'stores' in variant:
                                    for store in variant['stores']:
                                        store['price'] = float(precio_unitario)
                            
                            print("Payload para actualización:")
                            print(update_payload)
                            
                            # Enviar la actualización a Loyverse
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