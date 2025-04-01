import logging
import time
import datetime
import enum
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import requests
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Usar Enum para los estados de las tareas para mayor robustez
class TaskStatus(enum.Enum):
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED" # Usado cuando la tarea es cancelada

class TaskProgressManager:
    """
    Clase utilitaria para gestionar el progreso de tareas asíncronas en Redis.
    Permite guardar y consultar el estado y progreso de las tareas.
    """

    @staticmethod
    def _get_progress_key(task_id: str) -> str:
        """Obtiene la clave para almacenar el progreso de una tarea en Redis"""
        return f"task_progress:{task_id}"

    @classmethod
    def set_progress(cls, task_id: str, current: int, total: int, status: TaskStatus = TaskStatus.PROGRESS, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Actualiza el progreso de una tarea

        Args:
            task_id (str): ID de la tarea de Celery
            current (int): Cantidad de elementos procesados
            total (int): Total de elementos a procesar
            status (TaskStatus): Estado actual de la tarea (usando el Enum)
            metadata (dict, optional): Información adicional sobre la tarea
        """
        if total <= 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)

        progress_data = {
            'task_id': task_id,
            'status': status.value, # Guardar el valor string del enum en Redis
            'current': current,
            'total': total,
            'percentage': percentage,
            'last_update': datetime.datetime.now(datetime.timezone.utc).isoformat(), # Usar UTC
            'metadata': metadata or {}
        }

        # Almacenar en Redis por 24 horas (86400 segundos)
        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)

        logger.debug(f"Progreso actualizado: Tarea {task_id} - {current}/{total} ({percentage}%) Status: {status.value}")
        return progress_data

    @classmethod
    def get_progress(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información actual sobre el progreso de una tarea"""
        return cache.get(cls._get_progress_key(task_id))

    @classmethod
    def set_completed(cls, task_id: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Marca una tarea como completada con éxito"""
        progress_data = cls.get_progress(task_id) or {'task_id': task_id} # Asegurar que task_id esté
        progress_data.update({
            'status': TaskStatus.SUCCESS.value,
            'percentage': 100,
            'current': progress_data.get('total', progress_data.get('current', 0)), # Marcar current como total al completar
            'last_update': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'result': result or {},
            'error': None # Limpiar errores previos si los hubo
        })

        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        logger.info(f"Tarea {task_id} completada con éxito")
        return progress_data

    @classmethod
    def set_failed(cls, task_id: str, error: Optional[Any] = None) -> Dict[str, Any]:
        """Marca una tarea como fallida con el mensaje de error"""
        progress_data = cls.get_progress(task_id) or {'task_id': task_id}
        progress_data.update({
            'status': TaskStatus.FAILURE.value,
            'last_update': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'error': str(error) if error else "Error desconocido",
            'result': None # Limpiar resultados previos
        })

        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        logger.error(f"Tarea {task_id} fallida: {error}")
        return progress_data

    @classmethod
    def set_revoked(cls, task_id: str, message: str = "Tarea cancelada") -> Dict[str, Any]:
        """Marca una tarea como revocada/cancelada"""
        progress_data = cls.get_progress(task_id) or {'task_id': task_id}
        progress_data.update({
            'status': TaskStatus.REVOKED.value,
            'last_update': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'error': message, # Usar 'error' para el mensaje de cancelación o añadir campo 'message'
            'result': None
        })

        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        logger.warning(f"Tarea {task_id} revocada: {message}")
        return progress_data


# --- TAREAS CELERY ---

@shared_task(bind=True)
def sincronizar_inventario(self, force: bool = False) -> Dict[str, Any]:
    """
    Tarea asíncrona para sincronizar el inventario con Loyverse

    Args:
        self: Instancia de la tarea (proporcionado por Celery gracias a bind=True)
        force (bool): Si es True, fuerza la sincronización completa

    Returns:
        dict: Resultado de la sincronización
    """
    task_id = self.request.id
    logger.info(f"Iniciando tarea de sincronización de inventario (ID: {task_id}), force={force}")

    # Inicializar progreso
    # Empezamos con total=1 para evitar división por cero hasta tener el total real
    TaskProgressManager.set_progress(
        task_id=task_id,
        current=0,
        total=1,
        status=TaskStatus.STARTED
    )

    try:
        # Configuración de la API de Loyverse
        headers = {
            "Authorization": f"Bearer {settings.LOYVERSE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        logger.info(f"Obteniendo cantidad total de inventario de Loyverse (Tarea: {task_id})")
        
        # Obtener el número total de productos para actualizar el progreso
        inventory_items = []
        
        try:
            # Primero, intentemos ver cuál es el token para depurar (ocultando la mayoría)
            token_preview = f"{settings.LOYVERSE_API_TOKEN[:5]}...{settings.LOYVERSE_API_TOKEN[-5:]}" if len(settings.LOYVERSE_API_TOKEN) > 10 else "[token_corto]"
            logger.info(f"Usando token Loyverse: {token_preview} (Tarea: {task_id})")
            
            # Configuración de la API de Loyverse
            headers = {
                "Authorization": f"Bearer {settings.LOYVERSE_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Primer intento: obtener datos del endpoint de inventario
            try:
                # Hacemos la petición a la API
                request_url = "https://api.loyverse.com/v1.0/inventory"
                logger.info(f"Haciendo petición a: {request_url} (Tarea: {task_id})")
                
                response = requests.get(
                    request_url,
                    headers=headers,
                    timeout=15 # Añadir timeout a la petición
                )
                
                # Loguear detalles de la respuesta
                logger.info(f"Respuesta API status: {response.status_code} (Tarea: {task_id})")
                
                # Si no es 200, mostrar el error
                if response.status_code != 200:
                    logger.error(f"Error en respuesta API: {response.text} (Tarea: {task_id})")
                    
                response.raise_for_status()
                data = response.json()
                
                # Loguear la estructura de los datos para depuración
                logger.info(f"Estructura de la respuesta: {list(data.keys())} (Tarea: {task_id})")
                inventory_items = data.get('inventory_levels', [])
                
                # Loguear los primeros items (si hay) para ver su estructura
                if inventory_items:
                    logger.info(f"Ejemplo primer item de inventory_levels: {inventory_items[0]} (Tarea: {task_id})")
                else:
                    logger.warning(f"No se encontraron items en inventory_levels (Tarea: {task_id})")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error al consultar endpoint inventory: {e} (Tarea: {task_id})")
                # Mostrar más detalles del error si es posible
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Detalles del error inventory/: Status {e.response.status_code}, Contenido: {e.response.text[:500]} (Tarea: {task_id})")
                
                # Si falló el endpoint de inventory, intentamos con el endpoint de items como fallback
                logger.warning(f"Intentando endpoint alternativo items/ como fallback porque inventory_levels falló (Tarea: {task_id})")
                
                try:
                    request_url = "https://api.loyverse.com/v1.0/items"
                    logger.info(f"Haciendo petición a: {request_url} (Tarea: {task_id})")
                    
                    # Al principio sólo pedimos cantidad para saber cuántos hay en total
                    count_response = requests.get(
                        request_url,
                        headers=headers,
                        params={"limit": 1},
                        timeout=15
                    )
                    count_response.raise_for_status()
                    count_data = count_response.json()
                    total_count = count_data.get('count', 0)
                    
                    logger.info(f"Total de productos encontrados en endpoint items/: {total_count} (Tarea: {task_id})")
                    
                    if total_count > 0:
                        # Inicializar lista para todos los items
                        all_items = []
                        
                        # Ahora obtenemos todos los productos usando paginación
                        cursor = None
                        page_size = 250 # Máximo permitido por la API
                        max_items = 0  # Por defecto sin límite, podría definirse como parámetro más adelante
                        items_iteration = 0
                        
                        logger.info(f"Iniciando paginación con cursor. Tamaño de página: {page_size}, límite máximo: {max_items if max_items > 0 else 'sin límite'} (Tarea: {task_id})")
                        
                        while True:
                            items_iteration += 1
                            # Preparar parámetros de la petición
                            request_params = {"limit": page_size}
                            if cursor:
                                request_params["cursor"] = cursor
                                
                            # Hacer la petición para obtener este lote
                            logger.info(f"Solicitando lote #{items_iteration} con params: {request_params} (Tarea: {task_id})")
                            items_response = requests.get(
                                request_url,
                                headers=headers,
                                params=request_params,
                                timeout=30
                            )
                            items_response.raise_for_status()
                            items_data = items_response.json()
                            items = items_data.get('items', [])
                            
                            batch_count = len(items)
                            logger.info(f"Lote #{items_iteration}: Obtenidos {batch_count} productos, cursor: {cursor or 'inicial'} (Tarea: {task_id})")
                            
                            # Añadir los items a nuestra lista completa
                            all_items.extend(items)
                            total_so_far = len(all_items)
                            
                            logger.info(f"Total acumulado: {total_so_far} productos después del lote #{items_iteration} (Tarea: {task_id})")
                            
                            # Verificar si hay más páginas
                            cursor = items_data.get('cursor')
                            
                            # Verificar límites de paginación
                            if not cursor:
                                logger.info(f"Fin natural de la paginación, no hay más cursor. Total: {total_so_far} productos (Tarea: {task_id})")
                                break
                            
                            # Control de límite máximo si se especificó
                            if max_items > 0 and total_so_far >= max_items:
                                logger.info(f"Alcanzado el límite máximo configurado de {max_items} productos. Deteniendo paginación. (Tarea: {task_id})")
                                break
                            
                            # Si obtuvimos menos items que el tamaño de página, probablemente estamos en la última página
                            if batch_count < page_size:
                                logger.info(f"El lote tiene menos items ({batch_count}) que el tamaño de página ({page_size}). Probablemente última página. (Tarea: {task_id})")
                            
                            # Importante: pequeña pausa para no sobrecargar la API
                            time.sleep(0.5)
                        
                        # Ahora procesamos todos los items obtenidos
                        logger.info(f"Paginación completada. Total de productos obtenidos: {len(all_items)} en {items_iteration} lotes (Tarea: {task_id})")
                        
                        if all_items:
                            # Crear entradas de inventario manualmente para cada producto
                            for item in all_items:
                                variants = item.get('variants', [])
                                logger.debug(f"Producto {item.get('item_name')} tiene {len(variants)} variantes (Tarea: {task_id})")
                                
                                for variant in variants:
                                    variant_id = variant.get('id')
                                    # Para cada variante y tienda, creamos una entrada de inventario
                                    # Asumimos un valor predeterminado de stock si no está disponible
                                    inventory_items.append({
                                        'variant_id': variant_id,
                                        'store_id': settings.LOYVERSE_STORE_ID,  # Usar ID de la tienda configurada
                                        'in_stock': variant.get('inventory', {}).get('in_stock', 0),
                                        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
                                    })
                        
                            logger.info(f"Creadas {len(inventory_items)} entradas de inventario a partir de items/ (Tarea: {task_id})")
                            
                            # Log para depuración
                            if inventory_items:
                                logger.info(f"Ejemplo primer item construido: {inventory_items[0]} (Tarea: {task_id})")
                    
                except requests.exceptions.RequestException as items_e:
                    logger.error(f"También falló el endpoint items/: {items_e} (Tarea: {task_id})")
                    if hasattr(items_e, 'response') and items_e.response:
                        logger.error(f"Detalles del error items/: Status {items_e.response.status_code}, Contenido: {items_e.response.text[:500]} (Tarea: {task_id})")
            
            # Sea cual sea el método que funcionó, continuamos con el procesamiento
            total_items = len(inventory_items)
            
        except Exception as general_e:
            # Capturar cualquier otro error inesperado
            logger.exception(f"Error general obteniendo datos de inventario: {general_e} (Tarea: {task_id})")
            total_items = 0

        logger.info(f"Total de items de inventario encontrados: {total_items} (Tarea: {task_id})")

        # Si no hay items, terminar temprano
        if total_items == 0:
            result = {"success": True, "processed_items": 0, "total_items": 0, "message": "No hay productos para sincronizar."}
            TaskProgressManager.set_completed(task_id, result)
            logger.info(f"No hay productos para procesar, finalizando (Tarea: {task_id})")
            return result

        # Actualizar el total real
        TaskProgressManager.set_progress(
            task_id=task_id,
            current=0,
            total=total_items,
            status=TaskStatus.PROGRESS
        )

        # Procesamos directamente los items de inventario que ya obtuvimos
        processed_items = 0
        
        # ----------------------------------------------------------
        # ----- INICIO: LÓGICA DE PROCESAMIENTO DE CADA ITEM -----
        # ----------------------------------------------------------
        for item in inventory_items:
            # Verificar si la tarea ha sido cancelada
            # Mejor usar estado almacenado en Redis para evitar problemas con is_revoked
            task_status = TaskProgressManager.get_progress(task_id)
            if task_status and task_status.get('status') == TaskStatus.REVOKED.value:
                logger.warning(f"Tarea cancelada durante procesamiento de inventario (ID: {task_id})")
                return {"success": False, "message": "Tarea cancelada por el usuario"}

            variant_id = item.get('variant_id')
            store_id = item.get('store_id')
            in_stock = item.get('in_stock')
            updated_at = item.get('updated_at')
            
            logger.info(f"Procesando item de inventario - Variant ID: {variant_id}, Store: {store_id}, Stock: {in_stock} (Tarea: {task_id})")

            # Actualizar en la base de datos
            try:
                from facturacion.models import Producto
                producto = Producto.objects.filter(variant_id=variant_id).first()
                if producto:
                    # Log para ver qué producto estamos actualizando
                    logger.info(f"Actualizando producto en BD: ID={producto.id}, Nombre={producto.nombre}, Stock anterior={producto.stock_actual}, Nuevo stock={in_stock} (Tarea: {task_id})")
                    producto.stock_actual = in_stock
                    if updated_at:
                        try:
                            producto.ultima_actualizacion_stock = datetime.datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        except (ValueError, TypeError) as date_error:
                            logger.warning(f"Error al parsear fecha {updated_at}: {date_error}. Usando fecha actual. (Tarea: {task_id})")
                            producto.ultima_actualizacion_stock = datetime.datetime.now(datetime.timezone.utc)
                    else:
                        producto.ultima_actualizacion_stock = datetime.datetime.now(datetime.timezone.utc)
                    
                    # Actualizar fuente de actualización
                    producto.fuente_actualizacion = 'loyverse'
                    
                    producto.save(update_fields=['stock_actual', 'ultima_actualizacion_stock', 'fuente_actualizacion'])
                    logger.info(f"Producto con ID={producto.id} actualizado correctamente. Nuevo stock={in_stock} (Tarea: {task_id})")
                else:
                    logger.warning(f"No se encontró producto con variant_id={variant_id} en la BD local (Tarea: {task_id})")
            except Exception as item_error:
                logger.error(f"Error procesando item de inventario {variant_id}: {item_error}. Saltando item. (Tarea: {task_id})")
                # Consideramos saltar el item y continuar con los demás
            
            # Actualizar contador
            processed_items += 1
            
            # Actualizar progreso en Redis cada N items para no sobrecargar
            if processed_items % 10 == 0 or processed_items == total_items:
                progress_perc = int((processed_items / total_items) * 100) if total_items > 0 else 0
                logger.debug(f"Progreso: {processed_items}/{total_items} ({progress_perc}%) (Tarea: {task_id})")
                TaskProgressManager.set_progress(
                    task_id=task_id,
                    current=processed_items,
                    total=total_items,
                    status=TaskStatus.PROGRESS,
                    metadata={"last_processed_variant_id": variant_id}
                )
        # ----------------------------------------------------------
        # ----- FIN: LÓGICA DE PROCESAMIENTO DE CADA ITEM -----
        # ----------------------------------------------------------

        # Marcar como completada
        result = {
            "success": True,
            "processed_items": processed_items,
            "total_items": total_items
        }
        logger.info(f"Sincronización de inventario completada: {processed_items}/{total_items} productos procesados (Tarea: {task_id})")
        TaskProgressManager.set_completed(task_id, result)
        return result

    except SoftTimeLimitExceeded:
        error_msg = "La tarea excedió el tiempo límite permitido"
        logger.error(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        # Captura cualquier otra excepción no esperada
        error_msg = f"Error inesperado durante la sincronización: {str(e)}"
        logger.exception(f"{error_msg} (Tarea: {task_id})") # logger.exception incluye traceback
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}


@shared_task(bind=True, soft_time_limit=1800, time_limit=1900)  # 30 min soft, ~32 min hard
def sincronizar_precios(self, opciones: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tarea asíncrona para sincronizar precios con Loyverse
    
    Args:
        self: Instancia de la tarea (proporcionado por Celery)
        opciones (dict, optional): Opciones para la sincronización de precios
        
    Returns:
        dict: Resultado de la sincronización
    """
    from facturacion.models import Producto
    from facturacion.services import LoyverseService
    
    task_id = self.request.id
    opciones = opciones or {}
    
    logger.info(f"Iniciando tarea de sincronización de precios (ID: {task_id}), opciones={opciones}")
    
    # Inicializar progreso
    TaskProgressManager.set_progress(
        task_id=task_id,
        current=0,
        total=1,  # Total temporal
        status=TaskStatus.STARTED,
        metadata={"tipo_tarea": "sincronizacion_precios", "opciones": opciones}
    )
    
    try:
        # Inicializar el servicio
        loyverse_service = LoyverseService()
        
        # Filtrar productos por opciones (categorías, tipo_tasa, etc.)
        productos_query = Producto.objects.filter(loyverse_id__isnull=False)
        
        if opciones.get('categorias'):
            productos_query = productos_query.filter(categoria__in=opciones['categorias'])
            
        if opciones.get('tipo_tasa'):
            productos_query = productos_query.filter(tipo_tasa=opciones['tipo_tasa'])
            
        if opciones.get('productos_ids'):
            productos_query = productos_query.filter(id__in=opciones['productos_ids'])
            
        # Contar total de productos a procesar
        total_productos = productos_query.count()
        logger.info(f"Total de productos a procesar: {total_productos} (Tarea: {task_id})")
        
        if total_productos == 0:
            logger.warning(f"No se encontraron productos para procesar (Tarea: {task_id})")
            return {"success": False, "message": "No se encontraron productos para procesar"}
        
        # Actualizar progreso con el total real
        TaskProgressManager.set_progress(
            task_id=task_id,
            current=0,
            total=total_productos,
            status=TaskStatus.PROGRESS
        )
        
        # Calcular tamaño de lote según opciones o usar valor predeterminado
        tamaño_lote = opciones.get('tamaño_lote', 10)
        
        # Dividir productos en lotes para procesar
        productos_procesados = 0
        exito_total = True
        productos_actualizados = 0
        productos_fallidos = 0
        
        # Procesar por lotes para evitar timeout
        for i in range(0, total_productos, tamaño_lote):
            # Verificar si la tarea ha sido cancelada
            task_status = TaskProgressManager.get_progress(task_id)
            if task_status and task_status.get('status') == TaskStatus.REVOKED.value:
                logger.warning(f"Tarea de sincronización cancelada por el usuario (Tarea: {task_id})")
                return {"success": False, "message": "Tarea cancelada por el usuario"}
            
            # Obtener el siguiente lote de productos
            lote_productos = list(productos_query[i:i+tamaño_lote])
            logger.info(f"Procesando lote {i//tamaño_lote + 1}/{(total_productos + tamaño_lote - 1)//tamaño_lote}, productos {i+1}-{min(i+tamaño_lote, total_productos)} (Tarea: {task_id})")
            
            # Sincronizar este lote con Loyverse
            resultado_lote = loyverse_service.sync_prices(lote_productos)
            logger.info(f"Resultado del lote: {resultado_lote} (Tarea: {task_id})")
            
            # Actualizar contadores
            productos_procesados += len(lote_productos)
            productos_actualizados += resultado_lote.get('updated', 0)
            productos_fallidos += resultado_lote.get('failed', 0)
            
            # Si este lote falló, registrar pero continuar con los siguientes
            if not resultado_lote.get('success', False):
                exito_total = False
                logger.warning(f"Fallo en lote {i//tamaño_lote + 1}: {resultado_lote} (Tarea: {task_id})")
            
            # Actualizar progreso
            TaskProgressManager.set_progress(
                task_id=task_id,
                current=productos_procesados,
                total=total_productos,
                status=TaskStatus.PROGRESS,
                metadata={
                    "ultimo_lote": i//tamaño_lote + 1,
                    "resultado_lote": resultado_lote,
                    "productos_actualizados": productos_actualizados,
                    "productos_fallidos": productos_fallidos
                }
            )
            
            # Breve pausa para evitar sobrecargar la API
            time.sleep(1)
        
        # Marcar como completada
        result = {
            "success": exito_total,
            "processed_items": productos_procesados,
            "total_items": total_productos,
            "productos_actualizados": productos_actualizados,
            "productos_fallidos": productos_fallidos,
            "options": opciones
        }
        
        logger.info(f"Sincronización de precios completada: {productos_procesados}/{total_productos} productos (Tarea: {task_id})")
        TaskProgressManager.set_completed(task_id, result)
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = "La tarea excedió el tiempo límite permitido"
        logger.error(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error inesperado durante la sincronización de precios: {str(e)}"
        logger.exception(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}