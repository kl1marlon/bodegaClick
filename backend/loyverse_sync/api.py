"""
Utilidades para la comunicación con la API de Loyverse.

Incluye funciones para:
- Configuración de la API
- Gestión de reintentos automáticos
- Caché de respuestas para reducir llamadas
"""

import os
import requests
import logging
import time
import json
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configuración global
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos
CACHE_DURATION = 60 * 15  # 15 minutos en segundos
ITEMS_PER_PAGE = 250

# Caché en memoria para respuestas de la API
_api_cache = {}

def get_api_token():
    """Obtiene el token de API de Loyverse desde variables de entorno."""
    token = os.environ.get('LOYVERSE_API_TOKEN')
    if not token:
        logger.error("❌ No se encontró el token de API de Loyverse en variables de entorno")
        raise ValueError("Token de API de Loyverse no configurado")
    return token

def get_headers():
    """Obtiene los headers necesarios para las peticiones a la API de Loyverse."""
    return {
        'Authorization': f'Bearer {get_api_token()}',
        'Content-Type': 'application/json'
    }

def with_retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Decorador para reintentar llamadas a la API en caso de error.
    
    Args:
        max_retries: Número máximo de reintentos
        delay: Tiempo de espera entre reintentos (segundos)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"❌ Error en la API después de {max_retries} intentos: {str(e)}")
                        raise
                    
                    # Esperar antes de reintentar (backoff exponencial)
                    wait_time = delay * (2 ** (retries - 1))
                    logger.warning(f"⚠️ Error en la API, reintentando en {wait_time}s ({retries}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

def with_cache(duration=CACHE_DURATION):
    """
    Decorador para cachear respuestas de la API.
    
    Args:
        duration: Duración del caché en segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crear una clave única para esta llamada específica
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Verificar si existe en el caché y no ha expirado
            if cache_key in _api_cache:
                cached_time, cached_result = _api_cache[cache_key]
                if datetime.now() - cached_time < timedelta(seconds=duration):
                    logger.debug(f"🔄 Usando respuesta cacheada para {func.__name__}")
                    return cached_result
            
            # Si no está en caché o ha expirado, llamar a la función original
            result = func(*args, **kwargs)
            
            # Guardar en caché
            _api_cache[cache_key] = (datetime.now(), result)
            
            return result
        return wrapper
    return decorator

@with_retry()
@with_cache()
def get_categories():
    """
    Obtiene todas las categorías de Loyverse.
    
    Returns:
        dict: Mapa de ID de categoría a nombre de categoría
    """
    logger.info("🔍 Obteniendo categorías desde Loyverse...")
    
    try:
        url = 'https://api.loyverse.com/v1.0/categories'
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error al obtener categorías: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            raise requests.RequestException(f"Error {response.status_code}: {response.text}")
        
        categories = response.json().get('categories', [])
        category_map = {cat['id']: cat['name'] for cat in categories}
        
        logger.info(f"✅ Obtenidas {len(category_map)} categorías")
        return category_map
        
    except requests.RequestException as e:
        logger.exception(f"❌ Error durante la obtención de categorías: {str(e)}")
        raise

@with_retry()
def get_all_products():
    """
    Obtiene todos los productos de Loyverse usando paginación.
    
    Returns:
        list: Lista de diccionarios con la información de cada producto
    """
    logger.info("🔍 Obteniendo productos desde Loyverse...")
    
    all_products = []
    cursor = None
    page = 1
    
    while True:
        try:
            url = 'https://api.loyverse.com/v1.0/items'
            params = {'limit': ITEMS_PER_PAGE}
            if cursor:
                params['cursor'] = cursor
                
            logger.info(f"📥 Obteniendo página {page} de productos (cursor: {cursor})...")
            response = requests.get(url, headers=get_headers(), params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Error al obtener productos: {response.status_code}")
                logger.error(f"Respuesta: {response.text}")
                raise requests.RequestException(f"Error {response.status_code}: {response.text}")
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
                
            all_products.extend(items)
            logger.info(f"✅ Obtenidos {len(items)} productos en página {page}. Total acumulado: {len(all_products)}")
            
            cursor = data.get('cursor')
            if not cursor:
                break
                
            page += 1
            time.sleep(1)  # Pausa para evitar limitaciones de la API
                
        except requests.RequestException as e:
            logger.exception(f"❌ Error durante la obtención de productos: {str(e)}")
            raise
    
    logger.info(f"✅ Proceso completado. Obtenidos {len(all_products)} productos en total.")
    return all_products

@with_retry()
def get_product_by_id(loyverse_id):
    """
    Obtiene un producto específico por su ID de Loyverse.
    
    Args:
        loyverse_id: ID del producto en Loyverse
        
    Returns:
        dict: Información del producto
    """
    logger.info(f"🔍 Obteniendo producto con ID {loyverse_id}...")
    
    try:
        url = f"https://api.loyverse.com/v1.0/items/{loyverse_id}"
        response = requests.get(url, headers=get_headers(), timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error al obtener producto: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            raise requests.RequestException(f"Error {response.status_code}: {response.text}")
        
        return response.json()
        
    except requests.RequestException as e:
        logger.exception(f"❌ Error al obtener producto {loyverse_id}: {str(e)}")
        raise

@with_retry()
def update_product_price(product_data):
    """
    Actualiza el precio de un producto en Loyverse.
    
    Args:
        product_data: Datos completos del producto, incluyendo variantes con precios actualizados
        
    Returns:
        dict: Respuesta de la API
    """
    logger.info(f"🔄 Actualizando producto {product_data.get('id', 'desconocido')}...")
    
    try:
        url = "https://api.loyverse.com/v1.0/items"
        headers = get_headers()
        
        response = requests.post(url, headers=headers, json=product_data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error al actualizar producto: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            raise requests.RequestException(f"Error {response.status_code}: {response.text}")
        
        logger.info(f"✅ Producto actualizado correctamente")
        return response.json()
        
    except requests.RequestException as e:
        logger.exception(f"❌ Error al actualizar producto: {str(e)}")
        raise

def clear_cache():
    """Limpiar el caché de respuestas de la API."""
    global _api_cache
    _api_cache = {}
    logger.info("🧹 Caché de API limpiado") 