import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from celery.result import AsyncResult
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .tasks.sync_tasks import (
    sincronizar_inventario,
    sincronizar_precios,
    TaskProgressManager,
    TASK_STATUS_REVOKED
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_tarea(request):
    """Inicia una nueva tarea asíncrona"""
    task_type = request.data.get('type')
    if not task_type:
        return Response(
            {'error': 'Se requiere el tipo de tarea'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parámetros específicos según el tipo de tarea
    params = request.data.get('params', {})
    
    # Iniciar la tarea según su tipo
    if task_type == 'sync_inventory':
        task = sincronizar_inventario.delay(force=params.get('force', False))
    elif task_type == 'sync_prices':
        task = sincronizar_precios.delay(opciones=params)
    else:
        return Response(
            {'error': f'Tipo de tarea no soportado: {task_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'success': True,
        'message': f'Tarea {task_type} iniciada correctamente',
        'task_id': task.id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_tarea(request, task_id):
    """Consulta el estado de una tarea"""
    # Primero intentar obtener el progreso desde Redis
    progress_data = TaskProgressManager.get_progress(task_id)
    
    if progress_data:
        return Response(progress_data)
    
    # Si no hay datos en Redis, consultar a Celery
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        response_data = {
            'task_id': task_id,
            'status': 'PENDING',
            'message': 'La tarea está pendiente'
        }
    elif result.state == 'STARTED':
        response_data = {
            'task_id': task_id,
            'status': 'STARTED',
            'message': 'La tarea está en proceso'
        }
    elif result.state == 'SUCCESS':
        response_data = {
            'task_id': task_id,
            'status': 'SUCCESS',
            'result': result.result
        }
    elif result.state == 'FAILURE':
        response_data = {
            'task_id': task_id,
            'status': 'FAILURE',
            'error': str(result.result) if result.result else 'Error desconocido'
        }
    elif result.state == 'REVOKED':
        response_data = {
            'task_id': task_id,
            'status': 'REVOKED',
            'message': 'La tarea fue cancelada'
        }
    else:
        response_data = {
            'task_id': task_id,
            'status': result.state,
            'message': 'Estado desconocido'
        }
    
    return Response(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def control_tarea(request, task_id):
    """Controla una tarea en ejecución (pausa, reanuda, cancela)"""
    action = request.data.get('action')
    if not action or action not in ['cancel']:
        return Response(
            {'error': 'Acción no válida. Use: cancel'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    result = AsyncResult(task_id)
    
    if action == 'cancel':
        result.revoke(terminate=True)
        
        # También actualizar el estado en Redis si está disponible
        progress_data = TaskProgressManager.get_progress(task_id)
        if progress_data:
            progress_data['status'] = TASK_STATUS_REVOKED
            progress_data['message'] = 'Tarea cancelada por el usuario'
            cache.set(TaskProgressManager._get_progress_key(task_id), progress_data, timeout=86400)
        
        return Response({
            'success': True,
            'message': 'Tarea cancelada correctamente'
        })
    
    return Response(
        {'error': 'Acción no soportada'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_tareas(request):
    """Lista todas las tareas activas y recientes"""
    # Esta es una implementación básica que busca en Redis
    # En una versión más completa, se podría usar la API de Celery o almacenar
    # un registro de tareas en la base de datos
    
    # Filtrar por tipo si se especifica
    task_type = request.query_params.get('type')
    
    # Lista de claves que podrían contener datos de progreso de tareas
    keys = cache.keys('task_progress:*')
    tasks = []
    
    for key in keys:
        progress_data = cache.get(key)
        if progress_data:
            # Si se especificó un tipo y no coincide, saltar esta tarea
            if task_type and progress_data.get('metadata', {}).get('task_type') != task_type:
                continue
            
            tasks.append(progress_data)
    
    # Ordenar por fecha de actualización (más reciente primero)
    tasks.sort(key=lambda x: x.get('last_update', ''), reverse=True)
    
    return Response({
        'count': len(tasks),
        'tasks': tasks
    }) 