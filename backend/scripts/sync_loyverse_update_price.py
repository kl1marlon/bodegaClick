#!/usr/bin/env python
"""
Script para actualizar el precio de un producto en Loyverse usando el precio_base local.
Solo actualiza un producto para pruebas, usando payload completo.
"""
import os
import sys
import django
import requests
from decimal import Decimal
from dotenv import load_dotenv
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno y configurar Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))
django.setup()

from facturacion.models import Producto

LOYVERSE_API_TOKEN = os.environ.get('LOYVERSE_API_TOKEN')
if not LOYVERSE_API_TOKEN:
    logger.error('No se encontró LOYVERSE_API_TOKEN en las variables de entorno')
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {LOYVERSE_API_TOKEN}',
    'Content-Type': 'application/json'
}

# --- Seleccionar un producto local para actualizar ---
producto = Producto.objects.exclude(loyverse_id__isnull=True).exclude(loyverse_id='').first()
if not producto:
    logger.error('No hay productos locales con loyverse_id para actualizar.')
    sys.exit(1)

logger.info(f"Producto local seleccionado: {producto.nombre} (loyverse_id={producto.loyverse_id})")

# --- Obtener info completa del producto desde Loyverse ---
item_url = f"https://api.loyverse.com/v1.0/items/{producto.loyverse_id}"
resp = requests.get(item_url, headers=HEADERS)
if resp.status_code != 200:
    logger.error(f"No se pudo obtener el producto de Loyverse: {resp.status_code} {resp.text}")
    sys.exit(1)

item_data = resp.json()

# --- Actualizar el precio en el payload ---
logger.info("📝 Preparando payload para actualizar...")
# Asumimos que solo hay un variant y un store para simplificar la prueba
if not item_data.get('variants'):
    logger.error('El producto de Loyverse no tiene variantes.')
    sys.exit(1)

variant = item_data['variants'][0]
variant_id = variant.get('variant_id') or variant.get('id')

# --- Capturar precio anterior de Loyverse ---
precio_anterior_loyverse = "No encontrado"
if 'stores' in variant and variant['stores']:
    precio_anterior_loyverse = variant['stores'][0].get('price', "No encontrado")
elif variant.get('default_price') is not None:
    precio_anterior_loyverse = variant.get('default_price', "No encontrado")

logger.info(f"💲 Precio anterior en Loyverse: {precio_anterior_loyverse}")
logger.info(f"💲 Nuevo precio local (precio_base): {producto.precio_base}")

# Actualizar default_price y precios en stores
variant['default_price'] = float(producto.precio_base)
if 'stores' in variant and variant['stores']:
    for store in variant['stores']:
        store['price'] = float(producto.precio_base)

# --- Preparar payload completo y hacer POST para actualizar ---
payload = item_data
logger.info(f"📤 Payload a enviar: {payload}")
update_url = f"https://api.loyverse.com/v1.0/items"
update_resp = requests.post(update_url, headers=HEADERS, json=payload)

if update_resp.status_code in (200, 201):
    logger.info(f"✅ Precio actualizado correctamente en Loyverse para {producto.nombre}")
    logger.debug(f"Respuesta de Loyverse: {update_resp.json()}")
else:
    logger.error(f"❌ Error actualizando precio: {update_resp.status_code}")
    logger.error(f"Respuesta completa de Loyverse: {update_resp.text}")
