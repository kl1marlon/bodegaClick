from celery import shared_task
from django.utils import timezone
import time
import requests
import os
import logging
import json
from decimal import Decimal
from math import floor

from django.db import transaction
from django.conf import settings

from .models import LoyverseUserConnection
from facturacion.models import Producto, TasaCambio

# It's better to have LOYVERSE_API_BASE_URL in settings or a constants file.
LOYVERSE_API_BASE_URL = os.environ.get('LOYVERSE_API_BASE_URL', 'https://api.loyverse.com/v1.0')

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def recalculate_user_base_prices_task(self, user_id):
    """
    Tarea Celery para recalcular los precios base de todos los productos de un usuario
    utilizando su tasa de cambio preferida (BCV o PARALELO) y aplicando reglas de redondeo.
    
    Args:
        user_id (int): ID del usuario cuyos productos se van a recalcular
    
    Returns:
        dict: Resumen de la operación con contadores y detalles
    """
    logger.info(f"[Celery Task recalculate_user_base_prices_task] Iniciando recálculo de precios para user_id={user_id}")
    
    # Inicializar contadores y resumen
    summary = {
        'total_products': 0,
        'updated_products': 0,
        'unchanged_products': 0,
        'errors': [],
        'status': 'processing',
        'details': {
            'updated': [],
            'unchanged': []
        }
    }
    
    try:
        # Obtener las tasas de cambio del usuario
        tasas = {}
        for tasa in TasaCambio.objects.filter(user_id=user_id).order_by('-fecha')[:2]:
            tasas[tasa.tipo] = tasa.valor
        
        # Verificar que existan ambas tasas
        if 'BCV' not in tasas:
            logger.warning(f"No se encontró tasa BCV para user_id={user_id}")
            tasas['BCV'] = Decimal('0.0')
        if 'PARALELO' not in tasas:
            logger.warning(f"No se encontró tasa PARALELO para user_id={user_id}")
            tasas['PARALELO'] = Decimal('0.0')
        
        logger.info(f"Tasas obtenidas para user_id={user_id}: BCV={tasas.get('BCV')}, PARALELO={tasas.get('PARALELO')}")
        
        # Obtener todos los productos del usuario
        productos = Producto.objects.filter(user_id=user_id)
        total_productos = productos.count()
        summary['total_products'] = total_productos
        
        logger.info(f"Procesando {total_productos} productos para user_id={user_id}")
        
        # Procesar cada producto
        for producto in productos:
            try:
                # Verificar si tiene precio_base_usd válido
                if producto.precio_base_usd is None or producto.precio_base_usd <= 0:
                    logger.debug(f"Producto {producto.id} ({producto.nombre}) no tiene precio_base_usd válido. Saltando.")
                    continue
                
                # Determinar qué tasa usar según el tipo_tasa del producto
                tipo_tasa = producto.tipo_tasa if producto.tipo_tasa in ['BCV', 'PARALELO'] else 'BCV'
                tasa_valor = tasas.get(tipo_tasa, Decimal('0.0'))
                
                if tasa_valor <= 0:
                    logger.warning(f"Tasa {tipo_tasa} no válida para producto {producto.id}. Saltando.")
                    summary['errors'].append({
                        'product_id': producto.id,
                        'product_name': producto.nombre,
                        'error': f"Tasa {tipo_tasa} no válida o es cero"
                    })
                    continue
                
                # Calcular nuevo precio base
                nuevo_precio_base = producto.precio_base_usd * tasa_valor
                
                # Aplicar redondeo especial
                nuevo_precio_base_redondeado = aplicar_redondeo_especial(nuevo_precio_base)
                
                # Verificar si el precio cambió
                if abs(producto.precio_base - nuevo_precio_base_redondeado) < 0.01:
                    # El precio no cambió significativamente
                    logger.debug(f"Producto {producto.id} ({producto.nombre}): Precio sin cambios ({producto.precio_base})")
                    summary['unchanged_products'] += 1
                    summary['details']['unchanged'].append({
                        'id': producto.id,
                        'name': producto.nombre,
                        'price': float(producto.precio_base),
                        'rate_type': tipo_tasa,
                        'rate_value': float(tasa_valor)
                    })
                else:
                    # Actualizar el precio
                    precio_anterior = producto.precio_base
                    producto.precio_base = nuevo_precio_base_redondeado
                    producto.ultima_actualizacion_precio = timezone.now()
                    producto.save(update_fields=['precio_base', 'ultima_actualizacion_precio'])
                    
                    logger.info(f"Producto {producto.id} ({producto.nombre}): Precio actualizado de {precio_anterior} a {nuevo_precio_base_redondeado}")
                    summary['updated_products'] += 1
                    summary['details']['updated'].append({
                        'id': producto.id,
                        'name': producto.nombre,
                        'old_price': float(precio_anterior),
                        'new_price': float(nuevo_precio_base_redondeado),
                        'rate_type': tipo_tasa,
                        'rate_value': float(tasa_valor)
                    })
            except Exception as e:
                logger.exception(f"Error procesando producto {producto.id}: {str(e)}")
                summary['errors'].append({
                    'product_id': producto.id,
                    'product_name': producto.nombre,
                    'error': str(e)
                })
        
        # Actualizar estado final
        summary['status'] = 'completed'
        if summary['errors']:
            summary['status'] = 'completed_with_errors'
        
        logger.info(f"Recálculo de precios completado para user_id={user_id}. "  
                   f"Total: {summary['total_products']}, "  
                   f"Actualizados: {summary['updated_products']}, "  
                   f"Sin cambios: {summary['unchanged_products']}, "  
                   f"Errores: {len(summary['errors'])}")
        
        return summary
    
    except Exception as e:
        logger.exception(f"Error general en recalculate_user_base_prices_task para user_id={user_id}: {str(e)}")
        summary['status'] = 'failed'
        summary['error_message'] = str(e)
        return summary

def aplicar_redondeo_especial(precio):
    """
    Aplica reglas de redondeo especiales a precios en bolívares, imitando la lógica del frontend.
    """
    try:
        precio = float(precio)
    except Exception:
        return precio
    # Redondear a 2 decimales
    precio = round(precio, 2)
    entero = floor(precio)
    decimal = precio - entero
    residuo = entero % 10
    termina_en_5o0 = residuo == 0 or residuo == 5
    # Si termina en 0 o 5 y no tiene decimales, mantener igual
    if termina_en_5o0 and decimal == 0:
        return float(entero)
    # Precios menores a 20
    if entero < 20:
        if entero < 5:
            if entero <= 2:
                return float(entero)
            else:
                return 5.0
        elif entero < 10:
            if entero == 5:
                return 5.0
            elif decimal > 0 and entero == 5:
                return 10.0
            elif entero > 5:
                return 10.0
        elif entero < 15:
            if entero == 10 or entero == 11:
                return 10.0
            else:
                return 15.0
        else:  # 15 <= entero < 20
            if entero == 15 or entero == 16:
                return 15.0
            else:
                return 20.0
    # Para 20 o más, redondear al múltiplo de 5 más cercano hacia arriba
    resto = entero % 5
    if resto == 0 and decimal == 0:
        return float(entero)
    proximo_multiplo_5 = entero + (5 - resto) if resto != 0 else entero
    return float(proximo_multiplo_5)

@shared_task(bind=True, max_retries=3, default_retry_delay=5*60) # 5 minutes delay between retries
def sync_user_prices_to_loyverse(self, loyverse_connection_id, check_only=False, force_lower_price=False):
    """
    Tarea Celery para sincronizar los precios de productos desde BodegaClick hacia Loyverse.
    
    Args:
        loyverse_connection_id (int): ID de la conexión LoyverseUserConnection
        check_only (bool): Si es True, solo verifica diferencias sin realizar cambios
        force_lower_price (bool): Si es True, actualiza precios incluso si el local es menor que el de Loyverse
    
    Returns:
        str: Mensaje con el resultado de la sincronización
    """
    try:
        connection = LoyverseUserConnection.objects.get(id=loyverse_connection_id)
    except LoyverseUserConnection.DoesNotExist:
        logger.error(f"[Celery Task sync_user_prices_to_loyverse] LoyverseUserConnection with ID {loyverse_connection_id} not found.")
        return f"Error: Loyverse Connection ID {loyverse_connection_id} not found."

    logger.info(f"[Celery Task sync_user_prices_to_loyverse] Iniciando sincronización para connection ID {connection.id}, User: {connection.user.username}")
    logger.info(f"Opciones: check_only={check_only}, force_lower_price={force_lower_price}")
    
    # Actualizar estado de la conexión
    connection.price_sync_status = LoyverseUserConnection.SyncStatus.SYNCING
    connection.last_price_sync_start_time = timezone.now()
    connection.last_price_sync_details = {
        'status': 'Inicializando sincronización...',
        'processed_items': 0,
        'updated_items': 0,
        'skipped_items': 0,
        'errors': [],
        'check_only': check_only,
        'force_lower_price': force_lower_price,
        'differences': []
    }
    connection.save(update_fields=['price_sync_status', 'last_price_sync_start_time', 'last_price_sync_details'])

    # Obtener token de acceso válido
    access_token = connection.get_valid_access_token()

    if not access_token:
        logger.error(f"[Celery Task sync_user_prices_to_loyverse] No se pudo obtener un token válido para connection ID {connection.id}. Marcando como TOKEN_INVALID.")
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.TOKEN_INVALID
        connection.last_price_sync_end_time = timezone.now()
        connection.last_error_message = "No se pudo obtener o refrescar el token de acceso de Loyverse."
        # Marcar la conexión como inactiva si el token falla persistentemente
        connection.is_active = False 
        connection.last_price_sync_details['status'] = 'Falló: Token inválido.'
        connection.last_price_sync_details['errors'].append({'item_sku': 'N/A', 'error': 'Token de acceso inválido'})
        connection.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_error_message', 'is_active', 'last_price_sync_details'])
        return f"Sincronización fallida: Token inválido para connection ID {connection.id}"

    # Inicializar reporte de sincronización
    sync_report = {
        'total_local_products': 0,
        'total_loyverse_items_fetched': 0,
        'items_processed': 0,
        'items_updated_in_loyverse': 0,
        'items_skipped_matching_price': 0,
        'items_skipped_higher_price': 0,
        'items_skipped_check_only': 0,
        'items_with_errors': 0,
        'errors': [],
        'differences': [],
        'status_message': 'Procesando...',
        'check_only': check_only,
        'force_lower_price': force_lower_price
    }

    try:
        # --- 1. Obtener productos locales del usuario ---
        logger.info(f"[Celery Task sync_user_prices_to_loyverse] Obteniendo productos locales para {connection.user.username}...")
        local_products = Producto.objects.filter(user=connection.user).exclude(loyverse_id__isnull=True).exclude(loyverse_id='')
        
        # Filtrar productos sin precio_base válido
        valid_local_products = [p for p in local_products if p.precio_base is not None and p.precio_base > 0]
        if len(local_products) != len(valid_local_products):
            logger.warning(f"Se excluyeron {len(local_products) - len(valid_local_products)} productos locales sin precio_base válido.")
        
        # Crear mapa de productos por loyverse_id
        local_product_map = {p.loyverse_id: p for p in valid_local_products}
        sync_report['total_local_products'] = len(local_product_map)
        
        logger.info(f"Encontrados {len(local_product_map)} productos locales válidos con loyverse_id.")
        
        if not local_product_map:
            logger.info(f"[Celery Task sync_user_prices_to_loyverse] No hay productos locales válidos para sincronizar para {connection.user.username}.")
            sync_report['status_message'] = "No hay productos locales válidos para sincronización."
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED
            connection.last_price_sync_details.update(sync_report)
            connection.save(update_fields=['price_sync_status', 'last_price_sync_details'])
            # Continuar al bloque finally para establecer end_time
            return f"Sincronización completada para {connection.user.username}. No hay productos para sincronizar."

        # --- 2. Obtener todos los items de Loyverse usando paginación ---
        logger.info(f"Obteniendo todos los productos de Loyverse para {connection.user.username}...")
        
        all_loyverse_items = []
        cursor = None
        page = 1
        headers_get = {'Authorization': f'Bearer {access_token}'}
        
        while True:
            try:
                url = f"{LOYVERSE_API_BASE_URL}/items"
                params = {'limit': 250}
                if cursor:
                    params['cursor'] = cursor
                
                logger.info(f"Obteniendo página {page} de productos Loyverse (cursor: {cursor})...")
                response = requests.get(url, headers=headers_get, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        logger.info("No hay más productos en esta página.")
                        break
                    
                    # Filtrar items eliminados
                    active_items = [item for item in items if not item.get('deleted_at')]
                    if len(active_items) < len(items):
                        logger.info(f"Se excluyeron {len(items) - len(active_items)} productos eliminados en Loyverse.")
                    
                    all_loyverse_items.extend(active_items)
                    logger.info(f"Obtenidos {len(active_items)} productos activos. Total acumulado: {len(all_loyverse_items)}")
                    
                    cursor = data.get('cursor')
                    if not cursor:
                        logger.info("Fin de la paginación.")
                        break
                    page += 1
                    time.sleep(0.5)  # Pausa breve entre páginas para evitar rate limiting
                else:
                    logger.error(f"Error obteniendo productos de Loyverse (página {page}): {response.status_code}")
                    logger.error(f"Respuesta: {response.text}")
                    sync_report['errors'].append({
                        'item_sku': 'N/A', 
                        'error': f'Error obteniendo productos de Loyverse (página {page}): {response.status_code}'
                    })
                    break
            except requests.exceptions.RequestException as e:
                logger.exception(f"Error de red durante la obtención de productos de Loyverse (página {page}):")
                sync_report['errors'].append({
                    'item_sku': 'N/A', 
                    'error': f'Error de red: {str(e)}'
                })
                break
            except Exception as e:
                logger.exception(f"Error inesperado durante la obtención de productos de Loyverse (página {page}):")
                sync_report['errors'].append({
                    'item_sku': 'N/A', 
                    'error': f'Error inesperado: {str(e)}'
                })
                break
        
        sync_report['total_loyverse_items_fetched'] = len(all_loyverse_items)
        logger.info(f"Total de productos activos obtenidos de Loyverse: {len(all_loyverse_items)}")
        
        if not all_loyverse_items:
            logger.warning("No se pudieron obtener productos de Loyverse. Terminando sincronización.")
            sync_report['status_message'] = "No se pudieron obtener productos de Loyverse."
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
            connection.last_price_sync_details.update(sync_report)
            connection.last_error_message = "No se pudieron obtener productos de Loyverse."
            connection.save(update_fields=['price_sync_status', 'last_price_sync_details', 'last_error_message'])
            return f"Sincronización fallida para {connection.user.username}. No se pudieron obtener productos de Loyverse."

        # --- 3. Procesar cada producto de Loyverse y actualizar si es necesario ---
        logger.info(f"\n⚙️  Iniciando procesamiento de {len(all_loyverse_items)} productos de Loyverse...")
        
        total_items_to_process = len(all_loyverse_items)
        
        for i, item_data in enumerate(all_loyverse_items):
            loyverse_id = item_data.get('id')
            item_name = item_data.get('item_name', 'Nombre Desconocido')
            
            logger.info(f"--- Producto {i+1}/{total_items_to_process}: {item_name} (ID: {loyverse_id}) ---")
            sync_report['items_processed'] += 1
            
            if not loyverse_id:
                logger.warning("   ⚠️ Item de Loyverse sin ID. Saltando.")
                continue
            
            # Buscar el producto local correspondiente
            local_product = local_product_map.get(loyverse_id)
            
            if not local_product:
                logger.info(f"   ℹ️ Producto no encontrado en la base de datos local. Saltando.")
                continue
            
            # Preparar datos para actualizar el precio
            try:
                # Capturar precio anterior y tipo de precio
                precio_anterior_loyverse = None
                precio_anterior_loyverse_str = "No encontrado"
                pricing_type = 'FIXED'  # Asumir FIXED por defecto
                
                try:
                    variant = item_data['variants'][0]
                    pricing_type = variant.get('default_pricing_type', 'FIXED')
                    logger.info(f"   ℹ️ Tipo de precio en Loyverse: {pricing_type}")
                    
                    # Extraer precio anterior
                    if 'stores' in variant and variant['stores']:
                        # Tomar precio de la primera tienda como referencia
                        store_price = variant['stores'][0].get('price')
                        if store_price is not None:
                            precio_anterior_loyverse_str = str(store_price)
                    elif variant.get('default_price') is not None:
                        precio_anterior_loyverse_str = str(variant.get('default_price'))
                    
                    # Convertir precio anterior a Decimal si se encontró
                    if precio_anterior_loyverse_str != "No encontrado":
                        try:
                            precio_anterior_loyverse = Decimal(precio_anterior_loyverse_str)
                        except Exception:
                            logger.warning(f"   ⚠️ No se pudo convertir el precio anterior '{precio_anterior_loyverse_str}' a Decimal.")
                            precio_anterior_loyverse = None  # Tratar como no comparable
                
                except (IndexError, KeyError, TypeError) as e:
                    logger.error(f"   ❌ Error procesando estructura de variantes/precios para {item_name}: {e}")
                    sync_report['errors'].append({
                        'item_id': loyverse_id,
                        'item_name': item_name,
                        'error': f"Error estructura variantes: {e}"
                    })
                    sync_report['items_with_errors'] += 1
                    continue
                
                nuevo_precio_local = local_product.precio_base
                logger.info(f"   💲 Precio anterior Loyverse: {precio_anterior_loyverse_str}")
                logger.info(f"   💲 Nuevo precio Local: {nuevo_precio_local}")
                
                # --- Lógica de Comparación y Decisión ---
                prices_match = False
                if precio_anterior_loyverse is not None:
                    # Comparar con tolerancia de 0.01
                    if abs(precio_anterior_loyverse - nuevo_precio_local) < 0.01:
                        prices_match = True
                
                if prices_match:
                    logger.info("   ✅ Los precios ya coinciden. Saltando.")
                    sync_report['items_skipped_matching_price'] += 1
                    continue
                
                loyverse_price_is_higher = False
                if precio_anterior_loyverse is not None and precio_anterior_loyverse > nuevo_precio_local:
                    loyverse_price_is_higher = True
                
                if loyverse_price_is_higher:
                    logger.warning(f"   ⚠️ El precio en Loyverse ({precio_anterior_loyverse}) es MAYOR que el precio local ({nuevo_precio_local}).")
                    if not force_lower_price:
                        logger.info("   🚫 Saltando actualización (use force_lower_price=True para anular).")
                        sync_report['items_skipped_higher_price'] += 1
                        
                        # Registrar diferencia para el reporte
                        sync_report['differences'].append({
                            'name': item_name,
                            'loyverse_id': loyverse_id,
                            'price_before': float(precio_anterior_loyverse),
                            'price_after': float(nuevo_precio_local),
                            'status': "Omitido (Mayor en Loyverse)"
                        })
                        continue
                    else:
                        logger.info("   ❗ Forzando actualización a precio local menor (force_lower_price=True).")
                
                # --- Si es check_only, reportar y salir antes de preparar payload ---
                if check_only:
                    action = "Actualizar" if not loyverse_price_is_higher or force_lower_price else "Omitir (Mayor en Loyverse)"
                    logger.info(f"   [CHECK ONLY] Acción propuesta: {action}")
                    sync_report['items_skipped_check_only'] += 1
                    
                    # Registrar diferencia para el reporte
                    sync_report['differences'].append({
                        'name': item_name,
                        'loyverse_id': loyverse_id,
                        'price_before': float(precio_anterior_loyverse) if precio_anterior_loyverse else None,
                        'price_after': float(nuevo_precio_local),
                        'status': f"Check Only: {action}"
                    })
                    continue
                
                # --- Preparar payload para la actualización ---
                # Clonar item_data para no modificar el original en memoria
                try:
                    payload = json.loads(json.dumps(item_data))
                except Exception as e:
                    logger.error(f"   ❌ Error clonando datos del item {item_name}: {e}")
                    sync_report['errors'].append({
                        'item_id': loyverse_id,
                        'item_name': item_name,
                        'error': f"Error interno (clonación): {e}"
                    })
                    sync_report['items_with_errors'] += 1
                    continue
                
                try:
                    variant_to_update = payload['variants'][0]
                    if pricing_type == 'VARIABLE':
                        logger.info("   ⚠️ Precio VARIABLE detectado. Estableciendo precios a null en payload.")
                        variant_to_update['default_price'] = None
                        if 'stores' in variant_to_update and variant_to_update['stores']:
                            for store in variant_to_update['stores']:
                                store['price'] = None
                    else:  # Precio Fijo
                        logger.info(f"   Tipo de precio FIJO. Estableciendo precio {nuevo_precio_local} en payload.")
                        variant_to_update['default_price'] = float(nuevo_precio_local)  # API espera float
                        if 'stores' in variant_to_update and variant_to_update['stores']:
                            for store in variant_to_update['stores']:
                                # Asegurarse que el tipo sea FIXED si vamos a poner precio
                                store['pricing_type'] = 'FIXED'
                                store['price'] = float(nuevo_precio_local)
                        # Si no hay 'stores', asegurarse que default_price está bien puesto
                        elif 'default_price' not in variant_to_update:
                            variant_to_update['default_price'] = float(nuevo_precio_local)
                
                except Exception as e:
                    logger.error(f"   ❌ Error preparando payload para {item_name}: {e}")
                    sync_report['errors'].append({
                        'item_id': loyverse_id,
                        'item_name': item_name,
                        'error': f"Error preparando payload: {e}"
                    })
                    sync_report['items_with_errors'] += 1
                    continue
                
                # --- Enviar actualización a Loyverse usando POST ---
                update_url = f"{LOYVERSE_API_BASE_URL}/items"
                headers_post = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Respetar el límite de tasa de la API (1 petición por segundo)
                time.sleep(1.05)  # Esperar un poco más de 1 segundo para estar seguros
                
                try:
                    update_resp = requests.post(update_url, headers=headers_post, json=payload, timeout=30)
                    
                    if update_resp.status_code in (200, 201):
                        logger.info(f"   ✅ Precio actualizado correctamente en Loyverse.")
                        sync_report['items_updated_in_loyverse'] += 1
                        
                        # Registrar diferencia para el reporte
                        sync_report['differences'].append({
                            'name': item_name,
                            'loyverse_id': loyverse_id,
                            'price_before': float(precio_anterior_loyverse) if precio_anterior_loyverse else None,
                            'price_after': float(nuevo_precio_local),
                            'status': "Actualizado"
                        })
                    elif update_resp.status_code == 429:  # Too Many Requests
                        retry_after = int(update_resp.headers.get("Retry-After", 60))  # segundos
                        logger.warning(f"   ⚠️ Límite de tasa alcanzado. Reintentando después de {retry_after}s")
                        # Celery's self.retry will re-queue the task.
                        raise self.retry(countdown=retry_after, exc=requests.exceptions.HTTPError("Rate limit hit", response=update_resp))
                    else:
                        logger.error(f"   ❌ Error al actualizar precio: {update_resp.status_code}")
                        logger.error(f"   Respuesta Loyverse: {update_resp.text}")
                        
                        # Intentar extraer mensaje de error de la respuesta JSON si existe
                        error_message = f"Error API {update_resp.status_code}"
                        try:
                            error_details = update_resp.json()
                            if 'errors' in error_details:
                                error_message += f": {json.dumps(error_details['errors'])} "
                        except json.JSONDecodeError:
                            pass  # Mantener mensaje genérico si no es JSON
                        
                        sync_report['errors'].append({
                            'item_id': loyverse_id,
                            'item_name': item_name,
                            'error': error_message
                        })
                        sync_report['items_with_errors'] += 1
                        
                        # Registrar diferencia para el reporte con error
                        sync_report['differences'].append({
                            'name': item_name,
                            'loyverse_id': loyverse_id,
                            'price_before': float(precio_anterior_loyverse) if precio_anterior_loyverse else None,
                            'price_after': float(nuevo_precio_local),
                            'status': f"Error: {error_message}"
                        })
                
                except requests.exceptions.RequestException as e:
                    logger.exception(f"   ❌ Excepción de red al enviar actualización para {item_name}:")
                    sync_report['errors'].append({
                        'item_id': loyverse_id,
                        'item_name': item_name,
                        'error': f"Excepción de red: {e}"
                    })
                    sync_report['items_with_errors'] += 1
                except Exception as e:
                    logger.exception(f"   ❌ Excepción inesperada al enviar actualización para {item_name}:")
                    sync_report['errors'].append({
                        'item_id': loyverse_id,
                        'item_name': item_name,
                        'error': f"Excepción inesperada: {e}"
                    })
                    sync_report['items_with_errors'] += 1
            
            except Exception as e:
                logger.exception(f"Error general procesando producto {loyverse_id} ({item_name}): {e}")
                sync_report['errors'].append({
                    'item_id': loyverse_id,
                    'item_name': item_name,
                    'error': f"Error general: {e}"
                })
                sync_report['items_with_errors'] += 1
            
            logger.info("---------------------------------------------------")

        # --- Actualizar estado final y resumen ---
        if check_only:
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED
            sync_report['status_message'] = 'Verificación completada (modo check-only).'
        elif sync_report['items_with_errors'] > 0:
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED_WITH_ERRORS
            sync_report['status_message'] = 'Sincronización completada con algunos errores.'
        else:
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED
            sync_report['status_message'] = 'Sincronización completada exitosamente.'
        
        # Preparar resumen para el log
        resumen = f"""\n🏁 Finalizado el proceso de sincronización para {connection.user.username}.\n
📊 Resumen:\n
   - Productos locales válidos: {sync_report['total_local_products']}\n
   - Productos de Loyverse procesados: {sync_report['items_processed']}\n
   - Productos actualizados exitosamente: {sync_report['items_updated_in_loyverse']}\n
   - Omitidos (precio ya coincidía): {sync_report['items_skipped_matching_price']}\n
   - Omitidos (precio mayor en Loyverse): {sync_report['items_skipped_higher_price']}\n
   - Omitidos (modo check-only): {sync_report['items_skipped_check_only']}\n
   - Productos con errores: {sync_report['items_with_errors']}\n"""
        
        logger.info(resumen)

    except requests.exceptions.HTTPError as e:
        # This handles HTTP errors not caught by the inner loop's 429 specific handling (e.g. during initial item fetch)
        # Or if self.retry within the loop raises an exception that isn't caught by Celery's retry mechanism (unlikely for HTTPError)
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] HTTP Error during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"HTTP Error during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'General HTTP Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to HTTP error.'
        # If a retry is raised from here, Celery handles it.
        # If max_retries is exceeded, Celery won't call the task again.
        # We might want to re-raise to let Celery know it was an exception if not using self.retry directly.
        # For now, we catch and log, then proceed to finally block.

    except requests.exceptions.RequestException as e:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] Request Exception during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"Network/Request Exception during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'General Request/Network Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to network/request error.'
        # Consider re-raising if Celery should retry based on this exception type.
        # raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] Unexpected error during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"Unexpected error during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'Unexpected Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to an unexpected error.'
        # No re-raise here, as it's an unexpected error. Let Celery handle based on task settings.

    finally:
        connection.last_price_sync_end_time = timezone.now()
        connection.last_price_sync_details.update(sync_report)
        connection.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_error_message', 'last_price_sync_details'])
        logger.info(f"[Celery Task sync_loyverse_prices_for_user] Sync finished for connection ID {connection.id}. Status: {connection.price_sync_status}")
        return f"Sync completed for {connection.id}. Status: {connection.price_sync_status}. Details: {connection.last_price_sync_details}"

# Example of how you might trigger this task (e.g., from a view or admin action):
# from .tasks import sync_loyverse_prices_for_user
# sync_loyverse_prices_for_user.delay(loyverse_connection_id=some_id)
