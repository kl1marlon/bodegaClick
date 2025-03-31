import logging
import time
import datetime
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Constantes para los resultados de las tareas
TASK_STATUS_STARTED = "STARTED"
TASK_STATUS_PROGRESS = "PROGRESS"
TASK_STATUS_SUCCESS = "SUCCESS"
TASK_STATUS_FAILURE = "FAILURE"
TASK_STATUS_REVOKED = "REVOKED"

class TaskProgressManager:
    """
    Clase utilitaria para gestionar el progreso de tareas asíncronas en Redis.
    Permite guardar y consultar el estado y progreso de las tareas.
    """
    
    @staticmethod
    def _get_progress_key(task_id):
        """Obtiene la clave para almacenar el progreso de una tarea en Redis"""
        return f"task_progress:{task_id}"
    
    @classmethod
    def set_progress(cls, task_id, current, total, status=TASK_STATUS_PROGRESS, metadata=None):
        """
        Actualiza el progreso de una tarea
        
        Args:
            task_id (str): ID de la tarea de Celery
            current (int): Cantidad de elementos procesados
            total (int): Total de elementos a procesar
            status (str): Estado actual de la tarea
            metadata (dict, optional): Información adicional sobre la tarea
        """
        if total <= 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)
        
        progress_data = {
            'task_id': task_id,
            'status': status,
            'current': current,
            'total': total,
            'percentage': percentage,
            'last_update': datetime.datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Almacenar en Redis por 24 horas (86400 segundos)
        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        
        logger.debug(f"Progreso actualizado: Tarea {task_id} - {current}/{total} ({percentage}%)")
        return progress_data
    
    @classmethod
    def get_progress(cls, task_id):
        """Obtiene información actual sobre el progreso de una tarea"""
        return cache.get(cls._get_progress_key(task_id))
    
    @classmethod
    def set_completed(cls, task_id, result=None):
        """Marca una tarea como completada con éxito"""
        progress_data = cls.get_progress(task_id) or {}
        progress_data.update({
            'status': TASK_STATUS_SUCCESS,
            'percentage': 100,
            'last_update': datetime.datetime.now().isoformat(),
            'result': result or {}
        })
        
        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        logger.info(f"Tarea {task_id} completada con éxito")
        return progress_data
    
    @classmethod
    def set_failed(cls, task_id, error=None):
        """Marca una tarea como fallida con el mensaje de error"""
        progress_data = cls.get_progress(task_id) or {}
        progress_data.update({
            'status': TASK_STATUS_FAILURE,
            'last_update': datetime.datetime.now().isoformat(),
            'error': str(error) if error else "Error desconocido"
        })
        
        cache.set(cls._get_progress_key(task_id), progress_data, timeout=86400)
        logger.error(f"Tarea {task_id} fallida: {error}")
        return progress_data


@shared_task(bind=True)
def sincronizar_inventario(self, force=False):
    """
    Tarea asíncrona para sincronizar el inventario con Loyverse
    
    Args:
        self: Instancia de la tarea (proporcionado por Celery)
        force (bool): Si es True, fuerza la sincronización completa
    
    Returns:
        dict: Resultado de la sincronización
    """
    task_id = self.request.id
    logger.info(f"Iniciando tarea de sincronización de inventario (ID: {task_id}), force={force}")
    
    # Inicializar progreso
    TaskProgressManager.set_progress(
        task_id=task_id,
        current=0,
        total=100,  # Valor inicial estimado, se actualizará después
        status=TASK_STATUS_STARTED
    )
    
    try:
        # Configuración de la API de Loyverse
        headers = {
            "Authorization": f"Bearer {settings.LOYVERSE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Obteniendo cantidad total de productos de Loyverse (Tarea: {task_id})")
        # Obtener el número total de productos para actualizar el progreso
        response = requests.get(
            "https://api.loyverse.com/v1.0/items",
            headers=headers,
            params={"limit": 1}
        )
        response.raise_for_status()
        
        data = response.json()
        total_items = data.get('count', 0)
        logger.info(f"Total de productos encontrados: {total_items} (Tarea: {task_id})")
        
        # Actualizar el total
        TaskProgressManager.set_progress(
            task_id=task_id,
            current=0,
            total=total_items,
            status=TASK_STATUS_PROGRESS
        )
        
        # Configuración de la sincronización
        processed_items = 0
        batch_size = 50
        cursor = None
        
        # Procesar en lotes
        while True:
            # Verificar si la tarea ha sido cancelada
            if self.request.is_revoked:
                logger.warning(f"Tarea de sincronización cancelada por el usuario (ID: {task_id})")
                TaskProgressManager.set_progress(
                    task_id=task_id,
                    current=processed_items,
                    total=total_items,
                    status=TASK_STATUS_REVOKED
                )
                return {"success": False, "message": "Tarea cancelada por el usuario"}
            
            # Parámetros para la petición
            params = {"limit": batch_size}
            if cursor:
                params["cursor"] = cursor
            
            # Hacer petición a la API con manejo de reintentos
            max_retries = 3
            retry_count = 0
            success = False
            
            logger.debug(f"Obteniendo lote de productos, cursor={cursor}, batch_size={batch_size} (Tarea: {task_id})")
            
            while retry_count < max_retries and not success:
                try:
                    response = requests.get(
                        "https://api.loyverse.com/v1.0/items",
                        headers=headers,
                        params=params
                    )
                    response.raise_for_status()
                    success = True
                except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Backoff exponencial
                    logger.warning(f"Error en petición (intento {retry_count}): {e}. Reintentando en {wait_time} segundos. (Tarea: {task_id})")
                    
                    if retry_count >= max_retries:
                        raise
                    
                    time.sleep(wait_time)
            
            # Procesar los datos recibidos
            data = response.json()
            items = data.get('items', [])
            logger.info(f"Recibidos {len(items)} productos en este lote (Tarea: {task_id})")
            
            # Procesar cada producto
            for item in items:
                # Aquí iría la lógica de procesamiento de cada producto
                # Esta es una versión simplificada
                
                # Simulamos un tiempo de procesamiento
                time.sleep(0.1)
                
                # Actualizar progreso
                processed_items += 1
                
                # Actualizar progreso cada 10 productos o cuando sea el último
                if processed_items % 10 == 0 or processed_items == total_items:
                    progress_perc = int((processed_items / total_items) * 100) if total_items > 0 else 0
                    logger.debug(f"Progreso: {processed_items}/{total_items} ({progress_perc}%) (Tarea: {task_id})")
                    TaskProgressManager.set_progress(
                        task_id=task_id,
                        current=processed_items,
                        total=total_items,
                        status=TASK_STATUS_PROGRESS,
                        metadata={"last_item_id": item.get('id')}
                    )
            
            # Verificar si hay más páginas
            cursor = data.get('cursor')
            if not cursor:
                logger.info(f"No hay más productos para procesar, finalizando (Tarea: {task_id})")
                break
        
        # Marcar como completada
        result = {
            "success": True,
            "processed_items": processed_items,
            "total_items": total_items
        }
        logger.info(f"Sincronización completada: {processed_items}/{total_items} productos (Tarea: {task_id})")
        TaskProgressManager.set_completed(task_id, result)
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = "La tarea excedió el tiempo límite permitido"
        logger.error(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error durante la sincronización: {str(e)}"
        logger.exception(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg}


@shared_task(bind=True)
def sincronizar_precios(self, opciones=None):
    """
    Tarea asíncrona para sincronizar precios con Loyverse
    
    Args:
        self: Instancia de la tarea (proporcionado por Celery)
        opciones (dict): Opciones para la sincronización de precios
    
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
        total=100,  # Valor inicial estimado
        status=TASK_STATUS_STARTED
    )
    
    try:
        # Aquí iría la implementación completa de sincronización de precios
        # Por ahora es una simulación
        
        total_items = 200  # Simulado
        logger.info(f"Total de productos a procesar: {total_items} (Tarea: {task_id})")
        
        TaskProgressManager.set_progress(
            task_id=task_id,
            current=0,
            total=total_items,
            status=TASK_STATUS_PROGRESS
        )
        
        # Simulación de procesamiento
        for i in range(total_items):
            # Verificar si la tarea ha sido cancelada
            if self.request.is_revoked:
                logger.warning(f"Tarea de sincronización de precios cancelada por el usuario (ID: {task_id})")
                TaskProgressManager.set_progress(
                    task_id=task_id,
                    current=i,
                    total=total_items,
                    status=TASK_STATUS_REVOKED
                )
                return {"success": False, "message": "Tarea cancelada por el usuario"}
            
            # Simular trabajo
            time.sleep(0.05)
            
            # Actualizar progreso cada 10 items
            if i % 10 == 0 or i == total_items - 1:
                progress_perc = int(((i + 1) / total_items) * 100) if total_items > 0 else 0
                logger.debug(f"Progreso: {i + 1}/{total_items} ({progress_perc}%) (Tarea: {task_id})")
                TaskProgressManager.set_progress(
                    task_id=task_id,
                    current=i + 1,
                    total=total_items,
                    status=TASK_STATUS_PROGRESS
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
        error_msg = f"Error durante la sincronización de precios: {str(e)}"
        logger.exception(f"{error_msg} (Tarea: {task_id})")
        TaskProgressManager.set_failed(task_id, error_msg)
        return {"success": False, "error": error_msg} 