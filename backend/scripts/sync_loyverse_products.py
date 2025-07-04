#!/usr/bin/env python
"""
Script de Sincronización Inicial de Productos desde Loyverse

Este script importa productos desde una cuenta Loyverse a la base de datos local,
calculando correctamente el precio base en USD y asegurando que todos los productos
tengan el tipo de tasa "PARALELO".

Uso:
    python sync_loyverse_products.py <tasa_cambio>

Argumentos:
    tasa_cambio: La tasa de cambio a utilizar para calcular el precio en USD.
                 Ejemplo: 35.5 (para una tasa de 35.5 VES por 1 USD)

Ejemplo:
    python sync_loyverse_products.py 35.5

Notas:
    - Requiere que las variables de entorno LOYVERSE_API_TOKEN y DJANGO_SETTINGS_MODULE estén configuradas.
    - La base de datos debe estar limpia antes de ejecutar este script (ver documentación).
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
                    # Especificar encoding UTF-8 para ambos handlers
                    handlers=[
                        logging.FileHandler("loyverse_initial_sync.log", encoding='utf-8'), 
                        logging.StreamHandler(stream=sys.stdout) # StreamHandler usará encoding de la consola
                    ])
logger = logging.getLogger(__name__)

# Configurar StreamHandler para usar UTF-8 si es posible
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    # En algunas terminales/entornos esto puede no ser posible
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
    parser = argparse.ArgumentParser(description='Sincronización inicial de productos desde Loyverse')
    parser.add_argument('tasa_cambio', type=float, help='Tasa de cambio para calcular precio en USD (ej: 35.5)')
    return parser.parse_args()

def get_category_map(api_token):
    """Obtener un mapa de IDs de categorías a nombres de categorías desde Loyverse"""
    logger.info("🔍 Obteniendo mapa de categorías...")
    
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

def check_empty_database():
    """Verificar si la base de datos está vacía antes de sincronizar"""
    from facturacion.models import Producto
    
    count = Producto.objects.count()
    if count > 0:
        logger.warning(f"⚠️ ADVERTENCIA: La base de datos ya contiene {count} productos.")
        logger.warning("⚠️ Se recomienda limpiar la base de datos antes de ejecutar la sincronización inicial.")
        logger.warning("⚠️ Consulta la documentación para instrucciones sobre cómo limpiar la base de datos.")
        
        confirm = input("¿Deseas continuar de todos modos? (s/N): ").lower()
        if confirm != 's':
            logger.info("❌ Sincronización cancelada por el usuario.")
            sys.exit(1)
        
        logger.info("⚠️ Continuando con la sincronización a pesar de la advertencia...")
    else:
        logger.info("✅ Base de datos vacía, procediendo con la sincronización inicial...")

def sync_products_from_loyverse(tasa_cambio):
    """Sincronizar productos desde Loyverse con precios en USD y tasa PARALELO"""
    logger.info(f"🔄 Iniciando sincronización inicial de productos...")
    logger.info(f"💱 Tasa de cambio utilizada: {tasa_cambio}")
    
    # Importar modelos de Django
    from facturacion.models import Producto
    
    # Verificar si la base de datos está vacía
    check_empty_database()
    
    # Obtener token de API
    api_token = os.environ.get('LOYVERSE_API_TOKEN')
    if not api_token:
        logger.error("❌ No se encontró el token de API de Loyverse en las variables de entorno")
        logger.error("❌ Asegúrate de configurar la variable LOYVERSE_API_TOKEN")
        return False
    
    # Obtener mapa de categorías
    category_map = get_category_map(api_token)
    
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
    
    # Contadores para estadísticas
    created_count = 0
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
        
        # Calcular precio base en USD (dividir precio de Loyverse por la tasa)
        precio_base_usd = Decimal('0')
        if precio_actualizado and precio_loyverse > 0:
            precio_base_usd = precio_loyverse / Decimal(str(tasa_cambio))
            precio_base_usd = precio_base_usd.quantize(Decimal('0.01'))  # Redondear a 2 decimales
        
        # Obtener fecha de actualización
        updated_at = None
        if product.get('updated_at'):
            updated_at = datetime.fromisoformat(product['updated_at'].replace('Z', '+00:00'))
        
        # Crear nuevo producto
        try:
            nuevo_producto = Producto(
                loyverse_id=loyverse_id,
                variant_id=variant_id,
                nombre=nombre,
                descripcion=descripcion,
                precio_base=precio_loyverse,  # Precio en moneda local (VES)
                precio_base_usd=precio_base_usd,  # Precio en USD calculado
                categoria=nombre_categoria,
                ultima_actualizacion_precio=updated_at or datetime.now(),
                fuente_actualizacion='loyverse',
                es_precio_variable=es_precio_variable,
                porcentaje_ganancia=30.00,  # Valor predeterminado
                tipo_tasa='PARALELO'  # Siempre PARALELO para pruebas
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
    
    # Resumen final
    logger.info("\n📊 Resumen de sincronización inicial:")
    logger.info(f"- Total productos en Loyverse: {len(all_loyverse_products)}")
    logger.info(f"- Categorías mapeadas: {len(category_map)}")
    logger.info(f"- Productos nuevos creados: {created_count}")
    logger.info(f"- Errores durante la sincronización: {error_count}")
    logger.info(f"- Tasa de cambio utilizada: {tasa_cambio}")
    logger.info(f"- Tipo de tasa configurada: PARALELO")
    
    return created_count > 0

def main():
    """Función principal"""
    # Configurar Django
    setup_django()
    
    # Parsear argumentos
    args = parse_arguments()
    tasa_cambio = args.tasa_cambio
    
    # Validar tasa de cambio
    if tasa_cambio <= 0:
        logger.error("❌ La tasa de cambio debe ser un número positivo mayor que cero")
        sys.exit(1)
    
    # Ejecutar sincronización
    success = sync_products_from_loyverse(tasa_cambio)
    
    if success:
        logger.info("✅ Sincronización inicial completada exitosamente")
    else:
        logger.error("❌ La sincronización inicial falló")
        sys.exit(1)

if __name__ == '__main__':
    main()
