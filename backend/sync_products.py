import os
import django
import requests
from decimal import Decimal
import time
from datetime import datetime, timedelta
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("loyverse_sync_productos.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Producto, Factura

def get_category_map():
    """Obtener un mapa de IDs de categorías a nombres de categorías desde Loyverse"""
    logger.info("🔍 Obteniendo mapa de categorías...")
    
    api_token = os.environ.get('LOYVERSE_API_TOKEN')
    if not api_token:
        logger.error("❌ No se encontró el token de Loyverse")
        return {}
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        url = 'https://api.loyverse.com/v1.0/categories'
        logger.info("📥 Consultando API de categorías...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error obteniendo categorías: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            return {}
        
        categories = response.json().get('categories', [])
        logger.info(f"✅ Obtenidas {len(categories)} categorías")
        
        # Crear mapa de ID a nombre
        category_map = {cat['id']: cat['name'] for cat in categories}
        logger.info(f"📋 Mapa de categorías creado con {len(category_map)} entradas")
        
        return category_map
        
    except Exception as e:
        logger.exception("❌ Error durante la obtención del mapa de categorías:")
        return {}

def sync_products(actualizar_precios=True):
    """Sincronizar productos desde Loyverse con precios y categorías
    
    Args:
        actualizar_precios (bool): Si es True, actualiza los precios de los productos.
    """
    logger.info(f"🔄 Iniciando sincronización de productos... Actualizar precios: {actualizar_precios}")
    
    # Obtener mapa de categorías
    category_map = get_category_map()
    
    api_token = os.environ.get('LOYVERSE_API_TOKEN')
    if not api_token:
        logger.error("❌ No se encontró el token de Loyverse")
        return
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Obtener todos los productos de Loyverse
    all_loyverse_products = []
    cursor = None
    
    # Recolectar todos los productos de Loyverse
    while True:
        try:
            url = 'https://api.loyverse.com/v1.0/items'
            params = {'limit': 250}
            if cursor:
                params['cursor'] = cursor
                
            logger.info(f"📥 Obteniendo productos de Loyverse (cursor: {cursor})...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                    
                all_loyverse_products.extend(items)
                logger.info(f"✅ Obtenidos {len(items)} productos. Total acumulado: {len(all_loyverse_products)}")
                
                cursor = data.get('cursor')
                if not cursor:
                    break
                    
                time.sleep(1)  # Pausa para evitar limitaciones de API
            else:
                logger.error(f"❌ Error obteniendo productos: {response.status_code}")
                logger.error(f"Respuesta: {response.text}")
                break
                
        except Exception as e:
            logger.exception("❌ Error durante la obtención de productos:")
            break
    
    # Obtener productos de la base de datos
    db_products = {prod.loyverse_id: prod for prod in Producto.objects.filter(loyverse_id__isnull=False)}
    
    # Contadores para estadísticas
    created_count = 0
    updated_count = 0
    price_updated_count = 0
    category_updated_count = 0
    
    # Procesar cada producto
    for product in all_loyverse_products:
        loyverse_id = product['id']
        nombre = product['item_name']
        descripcion = product.get('description', '')
        
        # Obtener nombre de categoría usando el mapa
        category_id = product.get('category_id')
        nombre_categoria = category_map.get(category_id) if category_id else None
        
        # Ignorar productos eliminados
        if product.get('deleted_at'):
            if loyverse_id in db_products:
                # Marcar como inactivo en lugar de borrar
                db_product = db_products[loyverse_id]
                db_product.save()
                logger.info(f"🚫 Producto marcado como inactivo: {nombre} (ID: {loyverse_id})")
            continue
        
        # Obtener precio del primer variante y primera tienda
        precio = Decimal('0')
        es_precio_variable = False
        precio_actualizado = False
        
        if product.get('variants'):
            variant = product['variants'][0]
            
            # Determinar si es precio variable basado en el tipo de precio
            precio_variable = variant.get('default_pricing_type') == 'VARIABLE'
            
            # Intentar obtener el precio de la primera tienda
            if variant.get('stores') and len(variant['stores']) > 0:
                store = variant['stores'][0]
                store_price = store.get('price')
                
                if store_price is not None:
                    try:
                        precio = Decimal(str(store_price))
                        es_precio_variable = precio_variable
                        precio_actualizado = True
                    except Exception as e:
                        logger.warning(f"⚠️ Error al convertir precio para {nombre}: {str(e)}")
            
            # Si no hay precio de tienda, intentar con el precio predeterminado
            elif not precio_actualizado and variant.get('default_price') is not None:
                try:
                    precio = Decimal(str(variant['default_price']))
                    es_precio_variable = precio_variable
                    precio_actualizado = True
                except Exception as e:
                    logger.warning(f"⚠️ Error al convertir precio predeterminado para {nombre}: {str(e)}")
        
        # Obtener fecha de actualización
        updated_at = None
        if product.get('updated_at'):
            updated_at = datetime.fromisoformat(product['updated_at'].replace('Z', '+00:00'))
        
        # Actualizar o crear producto
        try:
            if loyverse_id in db_products:
                # Actualizar producto existente
                db_product = db_products[loyverse_id]
                update_needed = False
                
                # Actualizar nombre y descripción
                if db_product.nombre != nombre or db_product.descripcion != descripcion:
                    db_product.nombre = nombre
                    db_product.descripcion = descripcion
                    update_needed = True
                
                # Actualizar nombre de categoría
                if db_product.categoria != nombre_categoria:
                    db_product.categoria = nombre_categoria
                    category_updated_count += 1
                    update_needed = True
                
                # Actualizar precio si es diferente y tenemos un precio válido y actualizar_precios es True
                if actualizar_precios and precio_actualizado and db_product.precio_base != precio:
                    db_product.precio_base = precio
                    db_product.ultima_actualizacion_precio = updated_at
                    db_product.fuente_actualizacion = 'loyverse'
                    price_updated_count += 1
                    update_needed = True
                
                # Actualizar estado de precio variable
                if db_product.es_precio_variable != es_precio_variable:
                    db_product.es_precio_variable = es_precio_variable
                    update_needed = True
                
                # Asegurar que aplicar_iva siempre sea False para productos sincronizados
                if hasattr(db_product, 'aplicar_iva'):
                    db_product.aplicar_iva = False
                    update_needed = True
                
                # Guardar si hubo cambios
                if update_needed:
                    db_product.save()
                    updated_count += 1
                    logger.info(f"✏️ Producto actualizado: {nombre} (ID: {loyverse_id})" + 
                               (", precio actualizado" if precio_actualizado and actualizar_precios else "") + 
                               (f", categoría: {nombre_categoria}" if nombre_categoria else ""))
            else:
                # Crear nuevo producto
                nuevo_producto = Producto(
                    loyverse_id=loyverse_id,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio_base=precio,
                    categoria=nombre_categoria,
                    ultima_actualizacion_precio=updated_at or datetime.now(),
                    fuente_actualizacion='loyverse',
                    es_precio_variable=es_precio_variable,
                    porcentaje_ganancia=30.00,  # Valor predeterminado
                    tipo_tasa='BCV'  # Valor predeterminado
                )
                
                # Asegurar que aplicar_iva esté establecido en False para nuevos productos
                if hasattr(nuevo_producto, 'aplicar_iva'):
                    nuevo_producto.aplicar_iva = False
                
                nuevo_producto.save()
                created_count += 1
                logger.info(f"➕ Nuevo producto creado: {nombre} (ID: {loyverse_id})" + 
                           (f", categoría: {nombre_categoria}" if nombre_categoria else ""))
                
        except Exception as e:
            logger.exception(f"❌ Error procesando producto {nombre} (ID: {loyverse_id}):")
    
    # Resumen final
    logger.info("\n📊 Resumen de sincronización:")
    logger.info(f"- Total productos en Loyverse: {len(all_loyverse_products)}")
    logger.info(f"- Categorías mapeadas: {len(category_map)}")
    logger.info(f"- Productos nuevos creados: {created_count}")
    logger.info(f"- Productos actualizados: {updated_count}")
    logger.info(f"- Precios actualizados: {price_updated_count}")
    logger.info(f"- Categorías de productos actualizadas: {category_updated_count}")
    logger.info(f"- Actualización de precios habilitada: {actualizar_precios}")
    
    # Retornar estadísticas para poder usarlas en la API
    return {
        'created': created_count,
        'updated': updated_count,
        'prices_updated': price_updated_count,
        'categories_updated': category_updated_count,
        'total_loyverse': len(all_loyverse_products),
        'actualizar_precios': actualizar_precios
    }

if __name__ == '__main__':
    logger.info("=== Iniciando sincronización completa ===\n")
    sync_products()
    logger.info("=== Sincronización completada ===\n")