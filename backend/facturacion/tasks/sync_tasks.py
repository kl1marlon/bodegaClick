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

        logger.info(f"Obteniendo cantidad total de productos de Loyverse (Tarea: {task_id})")
        # Obtener el número total de productos para actualizar el progreso
        try:
            response = requests.get(
                "https://api.loyverse.com/v1.0/items",
                headers=headers,
                params={"limit": 1},
                timeout=15 # Añadir timeout a la petición
            )
            response.raise_for_status()
            data = response.json()
            total_items = data.get('count', 0)
        except requests.exceptions.RequestException as e:
             logger.error(f"Error obteniendo el total de items de Loyverse: {e} (Tarea: {task_id})")
             # Podemos fallar aquí o continuar con un total desconocido (0)
             total_items = 0 # O manejar el error de forma diferente
             # Si fallamos aquí:
             # raise ConnectionError(f"No se pudo obtener el total de items de Loyverse: {e}") from e


        logger.info(f"Total de productos encontrados: {total_items} (Tarea: {task_id})")

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

        # Configuración de la sincronización
        processed_items = 0
        batch_size = 50  # Ajustar según necesidad y límites de API
        cursor = None

        # Procesar en lotes
        while True:
            # Verificar si la tarea ha sido cancelada (USANDO MÉTODO)
            if self.request.is_revoked:
                logger.warning(f"Tarea de sincronización cancelada por el usuario (ID: {task_id})")
                # Usar el nuevo método para marcar como revocada
                TaskProgressManager.set_revoked(task_id, "Tarea cancelada por el usuario")
                return {"success": False, "message": "Tarea cancelada por el usuario"}

            # Parámetros para la petición
            params = {"limit": batch_size}
            if cursor:
                params["cursor"] = cursor

            # Hacer petición a la API con manejo de reintentos
            max_retries = 3
            retry_count = 0
            response = None # Inicializar response

            logger.debug(f"Obteniendo lote de productos, cursor={cursor}, batch_size={batch_size} (Tarea: {task_id})")

            while retry_count < max_retries:
                try:
                    response = requests.get(
                        "https://api.loyverse.com/v1.0/items",
                        headers=headers,
                        params=params,
                        timeout=30 # Timeout más largo para obtener lotes
                    )
                    response.raise_for_status() # Lanza excepción para 4xx/5xx
                    break # Salir del bucle de reintentos si la petición fue exitosa
                except requests.exceptions.Timeout:
                    retry_count += 1
                    logger.warning(f"Timeout en petición (intento {retry_count+1}/{max_retries}). Reintentando... (Tarea: {task_id})")
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count # Backoff exponencial
                    logger.warning(f"Error en petición (intento {retry_count}/{max_retries}): {e}. Reintentando en {wait_time} segundos. (Tarea: {task_id})")

                    if retry_count >= max_retries:
                        logger.error(f"Máximo número de reintentos alcanzado para obtener lote. (Tarea: {task_id})")
                        raise # Relanzar la última excepción para que la tarea falle
                    time.sleep(wait_time)

            if response is None: # Si todos los reintentos fallaron sin excepción específica (poco probable pero seguro)
                 raise ConnectionError("No se pudo obtener respuesta de la API de Loyverse tras varios intentos.")

            # Procesar los datos recibidos
            data = response.json()
            items = data.get('items', [])
            logger.info(f"Recibidos {len(items)} productos en este lote (Tarea: {task_id})")

            if not items and cursor: # Si no vienen items pero había cursor, algo raro pasó o terminó justo
                 logger.warning(f"Se recibió un lote vacío con cursor={cursor}. Asumiendo fin de paginación. (Tarea: {task_id})")
                 break


            # ----------------------------------------------------------
            # ----- INICIO: LÓGICA DE PROCESAMIENTO DE CADA ITEM -----
            # ----------------------------------------------------------
            for item in items:
                 # Verificar revocación también dentro del bucle interno por si el lote es grande
                 if self.request.is_revoked:
                    logger.warning(f"Tarea cancelada durante procesamiento de lote (ID: {task_id})")
                    TaskProgressManager.set_revoked(task_id, "Tarea cancelada por el usuario")
                    return {"success": False, "message": "Tarea cancelada por el usuario"}

                 item_id = item.get('id')
                 item_name = item.get('item_name', 'N/A')
                 logger.debug(f"Procesando item ID: {item_id}, Nombre: {item_name} (Tarea: {task_id})")

                 # Aquí iría la lógica para buscar el producto en tu BD,
                 # obtener su variant_id si no lo tienes,
                 # consultar el inventario de esa variante,
                 # y actualizar tu modelo Producto en PostgreSQL.
                 # Ejemplo simplificado:
                 try:
                     # producto = Producto.objects.get(loyverse_id=item_id)
                     # variant_id = obtener_variant_id(item, headers) # Función auxiliar
                     # stock_actual = obtener_stock_loyverse(variant_id, headers) # Función auxiliar
                     # producto.stock_actual = stock_actual
                     # producto.ultima_actualizacion_stock = datetime.datetime.now(datetime.timezone.utc)
                     # producto.save(update_fields=['stock_actual', 'ultima_actualizacion_stock'])
                     time.sleep(0.05) # Simular trabajo con la BD y otras APIs
                     pass # Reemplazar con lógica real

                 except Exception as item_error:
                     logger.error(f"Error procesando item {item_id} ({item_name}): {item_error}. Saltando item. (Tarea: {task_id})")
                     # Considerar si saltar el item o fallar la tarea completa

                 # Actualizar contador
                 processed_items += 1

                 # Actualizar progreso en Redis cada N items o al final del lote/tarea
                 # para no sobrecargar Redis en cada item
                 if processed_items % 10 == 0 or processed_items == total_items or items.index(item) == len(items) - 1:
                     progress_perc = int((processed_items / total_items) * 100) if total_items > 0 else 0
                     logger.debug(f"Progreso: {processed_items}/{total_items} ({progress_perc}%) (Tarea: {task_id})")
                     TaskProgressManager.set_progress(
                         task_id=task_id,
                         current=processed_items,
                         total=total_items,
                         status=TaskStatus.PROGRESS,
                         metadata={"last_processed_item_id": item_id} # Metadato útil
                     )
            # ----------------------------------------------------------
            # ----- FIN: LÓGICA DE PROCESAMIENTO DE CADA ITEM -----
            # ----------------------------------------------------------


            # Verificar si hay más páginas
            cursor = data.get('cursor')
            if not cursor:
                logger.info(f"No hay más productos para procesar (cursor nulo), finalizando (Tarea: {task_id})")
                break

        # Asegurarse de que el progreso final sea 100% si todo salió bien
        if processed_items != total_items:
             logger.warning(f"El número de items procesados ({processed_items}) no coincide con el total inicial ({total_items}). Ajustando progreso final. (Tarea: {task_id})")
             # Podrías ajustar el total aquí si crees que cambió, o solo marcar 100%
             TaskProgressManager.set_progress(task_id, processed_items, processed_items, status=TaskStatus.PROGRESS) # Ajusta total al procesado


        # Marcar como completada
        result = {
            "success": True,
            "processed_items": processed_items,
            "total_items": total_items # O podrías devolver processed_items como total final
        }
        logger.info(f"Sincronización completada: {processed_items}/{total_items} productos procesados (Tarea: {task_id})")
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


@shared_task(bind=True)
def sincronizar_precios(self, opciones: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tarea asíncrona para sincronizar precios con Loyverse (Simulación)

    Args:
        self: Instancia de la tarea (proporcionado por Celery)
        opciones (dict, optional): Opciones para la sincronización de precios

    Returns:
        dict: Resultado de la sincronización
    """
    task_id = self.request.id
    opciones = opciones or {}

    logger.info(f"Iniciando tarea de sincronización de precios (ID: {task_id}), opciones={opciones}")

    # Inicializar progreso
    TaskProgressManager.set_progress(
        task_id=task_id,
        current=0,
        total=1, # Total inicial temporal
        status=TaskStatus.STARTED
    )

    try:
        # Aquí iría la implementación completa de sincronización de precios
        # Por ahora es una simulación

        total_items = 200 # Simulado - Deberías obtener esto de alguna manera
        logger.info(f"Total de productos a procesar (precios): {total_items} (Tarea: {task_id})")

        TaskProgressManager.set_progress(
            task_id=task_id,
            current=0,
            total=total_items,
            status=TaskStatus.PROGRESS
        )

        # Simulación de procesamiento
        for i in range(total_items):
            # Verificar si la tarea ha sido cancelada (USANDO MÉTODO)
            if self.request.is_revoked:
                logger.warning(f"Tarea de sincronización de precios cancelada por el usuario (ID: {task_id})")
                TaskProgressManager.set_revoked(task_id, "Tarea cancelada por el usuario")
                return {"success": False, "message": "Tarea cancelada por el usuario"}

            # Simular trabajo
            time.sleep(0.05)

            # Actualizar progreso cada 10 items o al final
            processed_items_count = i + 1
            if processed_items_count % 10 == 0 or processed_items_count == total_items:
                progress_perc = int((processed_items_count / total_items) * 100) if total_items > 0 else 0
                logger.debug(f"Progreso (precios): {processed_items_count}/{total_items} ({progress_perc}%) (Tarea: {task_id})")
                TaskProgressManager.set_progress(
                    task_id=task_id,
                    current=processed_items_count,
                    total=total_items,
                    status=TaskStatus.PROGRESS
                )

        # Marcar como completada
        result = {
            "success": True,
            "processed_items": total_items,
            "total_items": total_items,
            "options": opciones
        }
        logger.info(f"Sincronización de precios completada: {total_items}/{total_items} productos (Tarea: {task_id})")
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