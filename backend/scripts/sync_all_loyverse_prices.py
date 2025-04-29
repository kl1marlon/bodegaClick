#!/usr/bin/env python
"""
Script para actualizar los precios de TODOS los productos en Loyverse
usando el precio_base de la base de datos local.

Compara precios, omite si coinciden, y por defecto no actualiza si
el precio local es menor que el de Loyverse (a menos que se use --force-lower-price).
Incluye un modo --check-only para solo reportar diferencias.
"""
import os
import sys
import django
import requests
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
import logging
import time
import json
import argparse # Importar argparse

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
LOYVERSE_API_URL = 'https://api.loyverse.com/v1.0'

def get_local_products():
    """Obtiene todos los productos locales con loyverse_id."""
    logger.info("📦 Obteniendo productos de la base de datos local...")
    local_products = Producto.objects.exclude(loyverse_id__isnull=True).exclude(loyverse_id='')
    # Filtrar productos sin precio_base válido
    valid_local_products = [p for p in local_products if p.precio_base is not None]
    product_map = {p.loyverse_id: p for p in valid_local_products}
    if len(local_products) != len(valid_local_products):
        logger.warning(f"   ⚠️ Se excluyeron {len(local_products) - len(valid_local_products)} productos locales sin precio_base.")
    logger.info(f"✅ Encontrados {len(product_map)} productos locales válidos con loyverse_id.")
    return product_map

def get_all_loyverse_items():
    """Obtiene todos los items de Loyverse usando paginación."""
    all_items = []
    cursor = None
    page = 1
    logger.info("🛍️ Obteniendo todos los productos de Loyverse...")
    while True:
        try:
            url = f"{LOYVERSE_API_URL}/items"
            params = {'limit': 250}
            if cursor:
                params['cursor'] = cursor
            
            logger.info(f"   Página {page} (cursor: {cursor})...")
            response = requests.get(url, headers=HEADERS, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if not items:
                    logger.info("   No hay más productos en esta página.")
                    break
                
                # Filtrar items eliminados
                active_items = [item for item in items if not item.get('deleted_at')]
                if len(active_items) < len(items):
                     logger.info(f"   Se excluyeron {len(items) - len(active_items)} productos eliminados en Loyverse.")
                
                all_items.extend(active_items)
                logger.info(f"   Obtenidos {len(active_items)} productos activos. Total acumulado: {len(all_items)}")
                
                cursor = data.get('cursor')
                if not cursor:
                    logger.info("   Fin de la paginación.")
                    break
                page += 1
                time.sleep(0.5) # Pausa breve entre páginas
            else:
                logger.error(f"❌ Error obteniendo productos de Loyverse (página {page}): {response.status_code}")
                logger.error(f"Respuesta: {response.text}")
                # Decidir si continuar o parar en caso de error de página
                break # Parar si una página falla
        except requests.exceptions.RequestException as e:
            logger.exception(f"❌ Error de red durante la obtención de productos de Loyverse (página {page}):")
            break
        except Exception as e:
            logger.exception(f"❌ Error inesperado durante la obtención de productos de Loyverse (página {page}):")
            break
            
    logger.info(f"✅ Total de productos activos obtenidos de Loyverse: {len(all_items)}")
    return all_items

def update_loyverse_price(item_data, local_product, check_only=False, force_lower_price=False):
    """Prepara el payload y actualiza el precio de un item en Loyverse, aplicando lógica de comparación y flags."""
    loyverse_id = item_data['id']
    nombre_local = local_product.nombre
    nuevo_precio_local_dec = Decimal(str(local_product.precio_base))

    logger.info(f"🔄 Procesando producto: {nombre_local} (ID: {loyverse_id})")

    # Clonar item_data para no modificar el original en memoria
    try:
        payload = json.loads(json.dumps(item_data))
    except Exception as e:
        logger.error(f"   ❌ Error clonando datos del item {nombre_local}: {e}")
        return False, "Error interno (clonación)", None, None

    if not payload.get('variants'):
        logger.warning(f"   ⚠️ Producto {nombre_local} no tiene variantes en Loyverse. Saltando.")
        return False, "Sin variantes", None, None

    # --- Capturar precio anterior y tipo de precio --- 
    precio_anterior_loyverse_str = "No encontrado"
    precio_anterior_loyverse_dec = None
    pricing_type = 'FIXED' # Asumir FIXED por defecto
    try:
        variant = payload['variants'][0]
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
                precio_anterior_loyverse_dec = Decimal(precio_anterior_loyverse_str)
            except InvalidOperation:
                logger.warning(f"   ⚠️ No se pudo convertir el precio anterior '{precio_anterior_loyverse_str}' a Decimal.")
                precio_anterior_loyverse_dec = None # Tratar como no comparable

    except (IndexError, KeyError, TypeError) as e:
         logger.error(f"   ❌ Error procesando estructura de variantes/precios para {nombre_local}: {e}")
         return False, f"Error estructura variantes: {e}", None, None

    logger.info(f"   💲 Precio anterior Loyverse: {precio_anterior_loyverse_str}")
    logger.info(f"   💲 Nuevo precio Local: {nuevo_precio_local_dec}")

    # --- Lógica de Comparación y Decisión --- 
    prices_match = False
    if precio_anterior_loyverse_dec is not None:
        # Usar is_close si se necesita tolerancia, o == para Decimal exacto
        if precio_anterior_loyverse_dec == nuevo_precio_local_dec:
             prices_match = True

    if prices_match:
        logger.info("   ✅ Los precios ya coinciden. Saltando.")
        return False, "Precio ya coincide", precio_anterior_loyverse_dec, nuevo_precio_local_dec

    loyverse_price_is_higher = False
    if precio_anterior_loyverse_dec is not None and precio_anterior_loyverse_dec > nuevo_precio_local_dec:
        loyverse_price_is_higher = True

    if loyverse_price_is_higher:
         logger.warning(f"   ⚠️ El precio en Loyverse ({precio_anterior_loyverse_dec}) es MAYOR que el precio local ({nuevo_precio_local_dec}).")
         if not force_lower_price:
             logger.info("   🚫 Saltando actualización (use --force-lower-price para anular).")
             return False, "Precio mayor en Loyverse (omitido)", precio_anterior_loyverse_dec, nuevo_precio_local_dec
         else:
             logger.info("   ❗ Forzando actualización a precio local menor (--force-lower-price activado).")
    
    # --- Si es check_only, reportar y salir antes de preparar payload --- 
    if check_only:
        action = "Actualizar" if not loyverse_price_is_higher or force_lower_price else "Omitir (Mayor en Loyverse)"
        logger.info(f"   [CHECK ONLY] Acción propuesta: {action}")
        return False, "Modo Check Only", precio_anterior_loyverse_dec, nuevo_precio_local_dec

    # --- Preparar payload para la actualización (Solo si se debe actualizar) ---
    try:
        variant_to_update = payload['variants'][0]
        if pricing_type == 'VARIABLE':
            logger.info("   ⚠️ Precio VARIABLE detectado. Estableciendo precios a null en payload.")
            variant_to_update['default_price'] = None
            if 'stores' in variant_to_update and variant_to_update['stores']:
                for store in variant_to_update['stores']:
                    store['price'] = None
        else: # Precio Fijo
            logger.info(f"   Tipo de precio FIJO. Estableciendo precio {nuevo_precio_local_dec} en payload.")
            variant_to_update['default_price'] = float(nuevo_precio_local_dec) # API espera float
            if 'stores' in variant_to_update and variant_to_update['stores']:
                for store in variant_to_update['stores']:
                    # Asegurarse que el tipo sea FIXED si vamos a poner precio
                    store['pricing_type'] = 'FIXED'
                    store['price'] = float(nuevo_precio_local_dec)
            # Si no hay 'stores', asegurarse que default_price está bien puesto
            elif 'default_price' not in variant_to_update:
                 variant_to_update['default_price'] = float(nuevo_precio_local_dec)
                 
    except Exception as e:
         logger.error(f"   ❌ Error preparando payload para {nombre_local}: {e}")
         return False, f"Error preparando payload: {e}", precio_anterior_loyverse_dec, nuevo_precio_local_dec

    # --- Enviar actualización a Loyverse usando POST --- 
    update_url = f"{LOYVERSE_API_URL}/items"
    try:
        # logger.debug(f"   📤 Payload a enviar: {json.dumps(payload)}") # Descomentar para debug detallado
        update_resp = requests.post(update_url, headers=HEADERS, json=payload, timeout=30)

        if update_resp.status_code in (200, 201):
            logger.info(f"   ✅ Precio actualizado correctamente en Loyverse.")
            # logger.debug(f"   Respuesta Loyverse: {update_resp.json()}") # Descomentar para debug detallado
            return True, "Actualizado", precio_anterior_loyverse_dec, nuevo_precio_local_dec
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
                 pass # Mantener mensaje genérico si no es JSON
            return False, error_message, precio_anterior_loyverse_dec, nuevo_precio_local_dec
            
    except requests.exceptions.RequestException as e:
        logger.exception(f"   ❌ Excepción de red al enviar actualización para {nombre_local}:")
        return False, f"Excepción de red: {e}", precio_anterior_loyverse_dec, nuevo_precio_local_dec
    except Exception as e:
        logger.exception(f"   ❌ Excepción inesperada al enviar actualización para {nombre_local}:")
        return False, f"Excepción inesperada: {e}", precio_anterior_loyverse_dec, nuevo_precio_local_dec

def main(args):
    logger.info("🚀 Iniciando script de sincronización/verificación de precios en Loyverse...")
    if args.check_only:
        logger.info("***** MODO CHECK-ONLY ACTIVADO: No se realizarán cambios en Loyverse. *****")
    if args.force_lower_price:
        logger.info("***** OPCIÓN FORCE-LOWER-PRICE ACTIVADA: Se actualizarán precios aunque el local sea menor. *****")
        
    local_product_map = get_local_products()
    if not local_product_map:
        logger.warning("No hay productos locales válidos con loyverse_id. Terminando script.")
        return

    all_loyverse_items = get_all_loyverse_items()
    if not all_loyverse_items:
        logger.warning("No se pudieron obtener productos de Loyverse. Terminando script.")
        return

    # Contadores
    processed_count = 0
    updated_count = 0
    match_skipped_count = 0
    higher_skipped_count = 0
    check_only_skipped_count = 0
    error_count = 0
    
    # Para reporte
    differences = []

    total_items_to_process = len(all_loyverse_items)
    logger.info(f"\n⚙️  Iniciando procesamiento de {total_items_to_process} productos de Loyverse...")

    for i, item_data in enumerate(all_loyverse_items):
        processed_count += 1
        loyverse_id = item_data.get('id')
        item_name = item_data.get('item_name', 'Nombre Desconocido')

        logger.info(f"--- Producto {i+1}/{total_items_to_process}: {item_name} (ID: {loyverse_id}) ---")

        if not loyverse_id:
            logger.warning("   ⚠️ Item de Loyverse sin ID. Saltando.")
            # No contamos como error, es un skip
            continue

        local_product = local_product_map.get(loyverse_id)

        if not local_product:
            logger.info("   ℹ️ Producto no encontrado en la base de datos local. Saltando.")
            # No contamos como error
            continue
        
        # Procesar y/o actualizar precio
        success, reason, price_before, price_after = update_loyverse_price(
            item_data, 
            local_product, 
            check_only=args.check_only, 
            force_lower_price=args.force_lower_price
        )
        
        # Registrar diferencia si no coinciden y no es check_only
        if reason not in ["Precio ya coincide", "Modo Check Only"] and price_before is not None and price_after is not None:
            differences.append({
                'name': item_name,
                'loyverse_id': loyverse_id,
                'price_before': price_before,
                'price_after': price_after,
                'status': reason 
            })
            
        # Actualizar contadores según el resultado
        if success:
            updated_count += 1
        else:
            if reason == "Precio ya coincide":
                match_skipped_count += 1
            elif reason == "Precio mayor en Loyverse (omitido)":
                higher_skipped_count += 1
            elif reason == "Modo Check Only":
                 check_only_skipped_count +=1 # Contar los que se hubieran procesado
            else: # Errores reales
                error_count += 1
                logger.error(f"   ❌ Falló el procesamiento para {item_name}. Razón: {reason}")
        
        # Pausa para evitar rate limiting (incluso en check_only para simular tiempo)
        if not args.check_only:
             time.sleep(0.5) # Pausa solo si se hacen llamadas POST reales
        else:
             time.sleep(0.05) # Pausa muy corta en check_only
             
        logger.info("---------------------------------------------------")

    # --- Resumen Final --- 
    logger.info("\n🏁 Finalizado el proceso.")
    logger.info("📊 Resumen:")
    logger.info(f"   - Productos de Loyverse encontrados y procesados: {processed_count}")
    if not args.check_only:
        logger.info(f"   - Productos actualizados exitosamente: {updated_count}")
        logger.info(f"   - Omitidos (precio ya coincidía): {match_skipped_count}")
        logger.info(f"   - Omitidos (precio mayor en Loyverse): {higher_skipped_count}")
        logger.info(f"   - Productos con errores (ver logs): {error_count}")
    else:
        logger.info(f"   - [CHECK ONLY] Productos que se hubieran procesado: {check_only_skipped_count}")
        # Podríamos añadir más detalle al resumen de check_only si es necesario

    # Imprimir reporte de diferencias procesadas (útil sobre todo en check_only)
    if differences:
        logger.info("\n📋 Reporte de Diferencias Procesadas (o que se procesarían):")
        for diff in differences:
             logger.info(f"   - {diff['name']} (ID: {diff['loyverse_id']}): Antes={diff['price_before']} -> Después={diff['price_after']} (Estado: {diff['status']})")

    logger.info("===================================================")

if __name__ == '__main__':
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Sincroniza precios de productos locales con Loyverse.')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Ejecutar en modo de solo verificación. No se harán cambios en Loyverse, solo se reportarán diferencias.'
    )
    parser.add_argument(
        '--force-lower-price',
        action='store_true',
        help='Forzar la actualización incluso si el precio local es menor que el precio actual en Loyverse.'
    )
    args = parser.parse_args()
    
    main(args)
