#!/usr/bin/env python
"""
Script de Sincronización Bidireccional de Productos con Loyverse (OAuth2)

Este script implementa la sincronización mejorada de productos desde Loyverse a BodegaClick,
utilizando la autenticación OAuth2 y preservando valores importantes como precio_base_usd.

Uso:
    python sync_loyverse_products_oauth.py <user_id> <tasa_cambio> [--force]

Argumentos:
    user_id: ID del usuario cuya conexión Loyverse se utilizará
    tasa_cambio: La tasa de cambio a utilizar para calcular el precio en USD para productos nuevos
    --force: Opcional. Si se especifica, fuerza la actualización incluso si el precio local es menor

Ejemplo:
    python sync_loyverse_products_oauth.py 1 35.5
    python sync_loyverse_products_oauth.py 1 35.5 --force

Notas:
    - Requiere que el usuario tenga una conexión OAuth2 activa con Loyverse
    - Preserva el precio_base_usd para productos existentes
    - Implementa multi-tenancy completo (todos los productos se asocian al usuario)
"""

import os
import sys
import django
import requests
from decimal import Decimal
import time
from datetime import datetime
import logging
import json
import argparse
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("loyverse_sync.log", encoding='utf-8'), 
                        logging.StreamHandler(stream=sys.stdout)
                    ])
logger = logging.getLogger(__name__)

# Configurar StreamHandler para usar UTF-8 si es posible
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    logger.warning("No se pudo reconfigurar stdout/stderr a UTF-8.")

def setup_django():
    """Configurar Django para acceder a los modelos y cargar .env"""
    # Obtener el directorio 'backend' y la raíz del proyecto
    script_dir = os.path.dirname(__file__)
    backend_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_dir) # Raíz del proyecto

    # Añadir el directorio 'backend' al sys.path para que encuentre 'config.settings'
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)

    # Cargar variables del archivo .env desde la raíz del proyecto
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        logger.warning(f"⚠️ Archivo .env no encontrado en {dotenv_path}")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Sincronización bidireccional de productos con Loyverse (OAuth2)')
    parser.add_argument('user_id', type=int, help='ID del usuario cuya conexión Loyverse se utilizará')
    parser.add_argument('tasa_cambio', type=float, help='Tasa de cambio para calcular precio en USD (ej: 35.5)')
    parser.add_argument('--force', action='store_true', help='Forzar actualización incluso si el precio local es menor')
    return parser.parse_args()

def get_loyverse_connection(user_id):
    """Obtener la conexión Loyverse del usuario y validar que esté activa"""
    from loyverse_integration.models import LoyverseUserConnection
    
    try:
        connection = LoyverseUserConnection.objects.get(user_id=user_id)
        
        if not connection.is_active:
            logger.error(f"❌ La conexión Loyverse para el usuario {user_id} no está activa")
            return None
        
        # Obtener token válido (se refresca automáticamente si es necesario)
        access_token = connection.get_valid_access_token()
        
        if not access_token:
            logger.error(f"❌ No se pudo obtener un token válido para el usuario {user_id}")
            return None
        
        logger.info(f"✅ Conexión Loyverse activa para usuario {user_id} ({connection.loyverse_account_name})")
        return connection, access_token
    
    except LoyverseUserConnection.DoesNotExist:
        logger.error(f"❌ No existe conexión Loyverse para el usuario {user_id}")
        return None
    except Exception as e:
        logger.exception(f"❌ Error obteniendo conexión Loyverse para usuario {user_id}:")
        return None

def get_category_map(access_token):
    """Obtener un mapa de IDs de categorías a nombres de categorías desde Loyverse"""
    logger.info("🔍 Obteniendo mapa de categorías...")
    
    if not access_token:
        logger.error("❌ No se encontró token de acceso válido")
        return {}
    
    headers = {
        'Authorization': f'Bearer {access_token}',
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

def check_existing_products(user_id):
    """Verificar productos existentes del usuario y crear un mapa por loyverse_id"""
    from facturacion.models import Producto
    
    try:
        # Obtener todos los productos del usuario
        productos = Producto.objects.filter(user_id=user_id)
        count = productos.count()
        
        # Crear mapa de loyverse_id a producto
        producto_map = {p.loyverse_id: p for p in productos if p.loyverse_id}
        
        logger.info(f"ℹ️ Usuario {user_id} tiene {count} productos en la base de datos")
        logger.info(f"ℹ️ {len(producto_map)} productos tienen loyverse_id asignado")
        
        return producto_map
    except Exception as e:
        logger.exception(f"❌ Error verificando productos existentes para usuario {user_id}:")
        return {}

def sync_products_from_loyverse(user_id, tasa_cambio, force_update=False):
    """
    Sincronizar productos desde Loyverse con precios en USD y tasa PARALELO,
    preservando precio_base_usd para productos existentes
    """
    logger.info(f"🔄 Iniciando sincronización de productos para usuario {user_id}...")
    logger.info(f"💱 Tasa de cambio utilizada para productos nuevos: {tasa_cambio}")
    
    # Importar modelos de Django
    from facturacion.models import Producto
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Verificar que el usuario existe
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        logger.error(f"❌ El usuario con ID {user_id} no existe")
        return False
    
    # Obtener conexión Loyverse y token de acceso
    connection_result = get_loyverse_connection(user_id)
    if not connection_result:
        return False
    
    connection, access_token = connection_result
    
    # Obtener mapa de categorías
    category_map = get_category_map(access_token)
    
    # Obtener mapa de productos existentes
    existing_products = check_existing_products(user_id)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
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
    
    # Contadores para estadísticas
    created_count = 0
    updated_count = 0
    unchanged_count = 0
    error_count = 0
    
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
            logger.info(f"🚫 Producto ignorado (eliminado): {nombre} (ID: {loyverse_id})")
            continue
        
        # Obtener precio del primer variante y primera tienda
        precio_loyverse = Decimal('0')
        es_precio_variable = False
        precio_actualizado = False
        variant_id = None
        
        if product.get('variants'):
            variant = product['variants'][0]
            variant_id = variant.get('id')
            
            # Determinar si es precio variable basado en el tipo de precio
            precio_variable = variant.get('default_pricing_type') == 'VARIABLE'
            
            # Intentar obtener el precio de la primera tienda
            if variant.get('stores') and len(variant['stores']) > 0:
                store = variant['stores'][0]
                store_price = store.get('price')
                
                if store_price is not None:
                    try:
                        precio_loyverse = Decimal(str(store_price))
                        es_precio_variable = precio_variable
                        precio_actualizado = True
                    except Exception as e:
                        logger.warning(f"⚠️ Error al convertir precio para {nombre}: {str(e)}")
            
            # Si no hay precio de tienda, intentar con el precio predeterminado
            elif not precio_actualizado and variant.get('default_price') is not None:
                try:
                    precio_loyverse = Decimal(str(variant['default_price']))
                    es_precio_variable = precio_variable
                    precio_actualizado = True
                except Exception as e:
                    logger.warning(f"⚠️ Error al convertir precio predeterminado para {nombre}: {str(e)}")
        
        # Obtener fecha de actualización
        updated_at = None
        if product.get('updated_at'):
            updated_at = datetime.fromisoformat(product['updated_at'].replace('Z', '+00:00'))
        
        # Verificar si el producto ya existe
        if loyverse_id in existing_products:
            # Actualizar producto existente
            try:
                producto_existente = existing_products[loyverse_id]
                
                # Preservar precio_base_usd si existe
                precio_base_usd = producto_existente.precio_base_usd
                
                # Si el producto no tiene precio_base_usd o es cero, calcularlo
                if precio_base_usd is None or precio_base_usd <= 0:
                    precio_base_usd = precio_loyverse / Decimal(str(tasa_cambio))
                    precio_base_usd = precio_base_usd.quantize(Decimal('0.01'))
                
                # Actualizar campos del producto
                producto_existente.nombre = nombre
                producto_existente.descripcion = descripcion
                producto_existente.precio_base = precio_loyverse
                producto_existente.variant_id = variant_id
                producto_existente.categoria = nombre_categoria
                producto_existente.ultima_actualizacion_precio = updated_at or datetime.now()
                producto_existente.fuente_actualizacion = 'loyverse'
                producto_existente.es_precio_variable = es_precio_variable
                
                # Solo guardar si hubo cambios
                if (producto_existente.precio_base != precio_loyverse or 
                    producto_existente.nombre != nombre or
                    producto_existente.descripcion != descripcion or
                    producto_existente.categoria != nombre_categoria):
                    
                    producto_existente.save()
                    updated_count += 1
                    logger.info(f"🔄 Producto actualizado: {nombre} (ID: {loyverse_id})")
                    logger.info(f"   - Precio Loyverse: {precio_loyverse} VES")
                    logger.info(f"   - Precio USD preservado: {precio_base_usd} USD")
                else:
                    unchanged_count += 1
                    logger.info(f"✓ Producto sin cambios: {nombre} (ID: {loyverse_id})")
                
            except Exception as e:
                logger.exception(f"❌ Error actualizando producto {nombre} (ID: {loyverse_id}):")
                error_count += 1
        else:
            # Crear nuevo producto
            try:
                # Calcular precio base en USD para productos nuevos
                precio_base_usd = Decimal('0')
                if precio_actualizado and precio_loyverse > 0:
                    precio_base_usd = precio_loyverse / Decimal(str(tasa_cambio))
                    precio_base_usd = precio_base_usd.quantize(Decimal('0.01'))
                
                nuevo_producto = Producto(
                    user=user,  # Asociar al usuario correcto
                    loyverse_id=loyverse_id,
                    variant_id=variant_id,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio_base=precio_loyverse,
                    precio_base_usd=precio_base_usd,
                    categoria=nombre_categoria,
                    ultima_actualizacion_precio=updated_at or datetime.now(),
                    fuente_actualizacion='loyverse',
                    es_precio_variable=es_precio_variable,
                    porcentaje_ganancia=30.00,
                    tipo_tasa='PARALELO'
                )
                
                # Asegurar que aplicar_iva esté establecido en False
                if hasattr(nuevo_producto, 'aplicar_iva'):
                    nuevo_producto.aplicar_iva = False
                
                nuevo_producto.save()
                created_count += 1
                
                # Log detallado para verificación
                logger.info(f"➕ Nuevo producto creado: {nombre} (ID: {loyverse_id})")
                logger.info(f"   - Precio Loyverse: {precio_loyverse} VES")
                logger.info(f"   - Tasa aplicada: {tasa_cambio}")
                logger.info(f"   - Precio USD calculado: {precio_base_usd} USD")
                logger.info(f"   - Tipo tasa: PARALELO")
                if nombre_categoria:
                    logger.info(f"   - Categoría: {nombre_categoria}")
                    
            except Exception as e:
                logger.exception(f"❌ Error procesando producto {nombre} (ID: {loyverse_id}):")
                error_count += 1
    
    # Actualizar estado de sincronización en la conexión
    try:
        connection.price_sync_status = 'COMPLETED'
        if error_count > 0:
            connection.price_sync_status = 'COMPLETED_WITH_ERRORS'
        
        connection.last_price_sync_end_time = datetime.now()
        connection.last_price_sync_details = {
            'total_products': len(all_loyverse_products),
            'created': created_count,
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count,
            'timestamp': datetime.now().isoformat()
        }
        connection.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_price_sync_details'])
    except Exception as e:
        logger.exception(f"❌ Error actualizando estado de sincronización en la conexión:")
    
    # Resumen final
    logger.info("\n📊 Resumen de sincronización:")
    logger.info(f"- Total productos en Loyverse: {len(all_loyverse_products)}")
    logger.info(f"- Categorías mapeadas: {len(category_map)}")
    logger.info(f"- Productos nuevos creados: {created_count}")
    logger.info(f"- Productos actualizados: {updated_count}")
    logger.info(f"- Productos sin cambios: {unchanged_count}")
    logger.info(f"- Errores durante la sincronización: {error_count}")
    logger.info(f"- Tasa de cambio utilizada: {tasa_cambio}")
    
    return created_count > 0 or updated_count > 0

def main():
    """Función principal"""
    # Configurar Django
    setup_django()
    
    # Parsear argumentos
    args = parse_arguments()
    user_id = args.user_id
    tasa_cambio = args.tasa_cambio
    force_update = args.force
    
    # Validar tasa de cambio
    if tasa_cambio <= 0:
        logger.error("❌ La tasa de cambio debe ser un número positivo mayor que cero")
        sys.exit(1)
    
    # Ejecutar sincronización
    success = sync_products_from_loyverse(user_id, tasa_cambio, force_update)
    
    if success:
        logger.info("✅ Sincronización completada exitosamente")
    else:
        logger.error("❌ La sincronización falló")
        sys.exit(1)

if __name__ == '__main__':
    main()
