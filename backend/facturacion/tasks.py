
import logging
import time
from decimal import Decimal, ROUND_UP, InvalidOperation
import requests
from celery import shared_task
from django.db import transaction
from .models import Producto

logger = logging.getLogger(__name__)

# --- Funciones de Utilidad ---

def aplicar_redondeo_especial(precio):
    """
    Aplica reglas de redondeo especiales a precios en bolívares.
    """
    try:
        precio_dec = Decimal(str(precio))
    except (InvalidOperation, TypeError):
        return precio

    if precio_dec < 20:
        return (precio_dec / 5).quantize(Decimal('1'), rounding=ROUND_UP) * 5
    else:
        return (precio_dec / 5).quantize(Decimal('1'), rounding=ROUND_UP) * 5

class LoyverseAPIClient:
    """
    Un cliente simple para interactuar con la API de Loyverse.
    """
    def __init__(self, api_token):
        if not api_token:
            raise ValueError("El token de la API de Loyverse no puede estar vacío.")
        self.api_token = api_token
        self.base_url = 'https://api.loyverse.com/v1.0'
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def get_all_items(self):
        """Obtiene todos los items activos de Loyverse usando paginación."""
        all_items = []
        cursor = None
        page = 1
        logger.info("🛍️ Obteniendo todos los productos de Loyverse...")
        while True:
            try:
                url = f"{self.base_url}/items"
                params = {'limit': 250}
                if cursor:
                    params['cursor'] = cursor

                logger.info(f"   Página {page} (cursor: {cursor})...")
                response = requests.get(url, headers=self.headers, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        break
                    
                    active_items = [item for item in items if not item.get('deleted_at')]
                    all_items.extend(active_items)
                    
                    cursor = data.get('cursor')
                    if not cursor:
                        break
                    page += 1
                    time.sleep(0.5)
                else:
                    logger.error(f"❌ Error obteniendo productos de Loyverse (página {page}): {response.status_code} {response.text}")
                    break
            except requests.exceptions.RequestException as e:
                logger.exception(f"❌ Error de red durante la obtención de productos de Loyverse (página {page}):")
                break
        logger.info(f"✅ Total de productos activos obtenidos de Loyverse: {len(all_items)}")
        return all_items

    def update_item_price(self, payload):
        """Actualiza un item en Loyverse."""
        update_url = f"{self.base_url}/items"
        try:
            # Respetar el límite de la API
            time.sleep(1.05)
            response = requests.post(update_url, headers=self.headers, json=payload, timeout=30)
            return response
        except requests.exceptions.RequestException as e:
            logger.exception("Excepción de red al enviar actualización a Loyverse.")
            return None


# --- Tareas Celery ---

@shared_task(name='facturacion.recalcular_precios_base_locales')
def recalcular_precios_base_locales(tasa_bcv, tasa_paralelo):
    """
    Tarea Celery para recalcular el precio_base de todos los productos locales.
    """
    logger.info("Iniciando tarea: recalcular_precios_base_locales...")
    
    try:
        tasa_bcv = Decimal(tasa_bcv)
        tasa_paralelo = Decimal(tasa_paralelo)
    except InvalidOperation:
        logger.error("Tasas inválidas. Deben ser números decimales.")
        return {'error': 'Tasas inválidas.'}

    tasas = {'BCV': tasa_bcv, 'PARALELO': tasa_paralelo}
    
    productos_a_actualizar = []
    total_count = 0
    updated_count = 0
    
    productos = Producto.objects.filter(precio_base_usd__gt=0)
    total_count = productos.count()

    for producto in productos:
        tasa_a_usar = tasas.get(producto.tipo_tasa, tasas['BCV'])
        nuevo_precio_base = producto.precio_base_usd * tasa_a_usar
        nuevo_precio_redondeado = aplicar_redondeo_especial(nuevo_precio_base)

        if producto.precio_base != nuevo_precio_redondeado:
            producto.precio_base = nuevo_precio_redondeado
            productos_a_actualizar.append(producto)
            updated_count += 1

    if productos_a_actualizar:
        with transaction.atomic():
            Producto.objects.bulk_update(productos_a_actualizar, ['precio_base'])
        logger.info(f"Se actualizaron {len(productos_a_actualizar)} productos en lote.")

    resumen = {
        'revisados': total_count,
        'actualizados': updated_count,
        'sin_cambios': total_count - updated_count
    }
    logger.info(f"Resumen de recálculo: {resumen}")
    return resumen


@shared_task(bind=True, name='facturacion.sincronizar_precios_con_loyverse', max_retries=3, default_retry_delay=300)
def sincronizar_precios_con_loyverse(self, api_token, check_only=False, force_lower_price=False):
    """
    Tarea Celery para sincronizar los precios locales con Loyverse.
    """
    logger.info("Iniciando tarea: sincronizar_precios_con_loyverse...")
    client = LoyverseAPIClient(api_token)
    
    # Contadores
    procesados = 0
    actualizados = 0
    errores = 0
    omitidos_coincidencia = 0
    omitidos_precio_mayor = 0

    local_products_map = {p.loyverse_id: p for p in Producto.objects.exclude(loyverse_id__isnull=True).exclude(loyverse_id='')}
    loyverse_items = client.get_all_items()

    for item_data in loyverse_items:
        procesados += 1
        loyverse_id = item_data.get('id')
        local_product = local_products_map.get(loyverse_id)

        if not local_product or local_product.precio_base is None:
            continue

        try:
            variant = item_data['variants'][0]
            precio_loyverse_str = variant.get('stores', [{}])[0].get('price') or variant.get('default_price')
            precio_loyverse = Decimal(str(precio_loyverse_str)) if precio_loyverse_str is not None else None
            precio_local = Decimal(str(local_product.precio_base))

            if precio_loyverse == precio_local:
                omitidos_coincidencia += 1
                continue

            if precio_loyverse is not None and precio_loyverse > precio_local and not force_lower_price:
                omitidos_precio_mayor += 1
                continue

            if check_only:
                logger.info(f"[CHECK ONLY] Se actualizaría el producto {local_product.nombre} de {precio_loyverse} a {precio_local}")
                continue

            # Preparar y enviar actualización
            payload = item_data.copy()
            payload['variants'][0]['default_price'] = float(precio_local)
            if 'stores' in payload['variants'][0] and payload['variants'][0]['stores']:
                 payload['variants'][0]['stores'][0]['price'] = float(precio_local)

            response = client.update_item_price(payload)

            if response and response.status_code in (200, 201):
                actualizados += 1
            elif response and response.status_code == 429:
                logger.warning("Límite de peticiones alcanzado. Reintentando tarea...")
                self.retry(exc=Exception("Rate limit exceeded"))
            else:
                errores += 1
                logger.error(f"Error al actualizar {local_product.nombre}: {response.text if response else 'Sin respuesta'}")

        except (KeyError, IndexError, InvalidOperation) as e:
            errores += 1
            logger.error(f"Error procesando el producto {local_product.nombre}: {e}")
        except Exception as e:
            errores += 1
            logger.error(f"Error inesperado con el producto {local_product.nombre}: {e}")
            # Considerar reintentar en caso de errores inesperados
            self.retry(exc=e)

    resumen = {
        'procesados': procesados,
        'actualizados': actualizados,
        'errores': errores,
        'omitidos_coincidencia': omitidos_coincidencia,
        'omitidos_precio_mayor': omitidos_precio_mayor,
        'check_only_mode': check_only
    }
    logger.info(f"Resumen de sincronización: {resumen}")
    return resumen
