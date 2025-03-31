import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from celery.result import AsyncResult
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .tasks.sync_tasks import (
    sincronizar_inventario,
    sincronizar_precios,
    TaskProgressManager,
    TaskStatus
)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def iniciar_tarea(request):
    """Inicia una nueva tarea asíncrona"""
    # Verificar token de administrador si se trata de tareas sensibles
    task_type = request.data.get('type')
    if task_type in ['sync_inventory', 'sync_prices']:
        token = request.headers.get('X-Admin-Token')
        if token != settings.ADMIN_SECRET_TOKEN:
            return Response({'error': 'No autorizado'}, status=status.HTTP_401_UNAUTHORIZED)
    
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
@permission_classes([AllowAny])
def estado_tarea(request, task_id):
    """Consulta el estado de una tarea"""
    try:
        task_result = AsyncResult(task_id)
        
        # Obtener información del progreso desde Redis
        progress_data = TaskProgressManager.get_progress(task_id)
        
        if progress_data:
            # Datos de progreso disponibles en Redis
            return Response(progress_data)
        else:
            # Fallback a estado básico de Celery
            task_status = task_result.status
            task_result_value = task_result.result if task_result.ready() else None
            
            return Response({
                'task_id': task_id,
                'status': task_status,
                'result': task_result_value
            })
    except Exception as e:
        return Response(
            {'error': f'Error al consultar tarea: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
        
        # Usar el método set_revoked para actualizar el estado de forma consistente
        TaskProgressManager.set_revoked(task_id, "Tarea cancelada por el usuario")
        
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

@api_view(['GET'])
@permission_classes([AllowAny])
def test_cors(request):
    """Endpoint simple para probar configuración CORS"""
    return Response({
        'success': True,
        'message': 'La configuración CORS está funcionando correctamente',
        'headers_received': {
            'origin': request.headers.get('origin', 'No origin header'),
            'host': request.headers.get('host', 'No host header'),
            'x-admin-token': 'Presente' if request.headers.get('x-admin-token') else 'No presente'
        }
    }) 