from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
import logging

from .models import LoyverseUserConnection
from .serializers import LoyverseConnectionSerializer, SyncOptionsSerializer
from .tasks import recalculate_user_base_prices_task, sync_user_prices_to_loyverse
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

class LoyverseConnectionViewSet(viewsets.GenericViewSet):
    """
    API para interactuar con la conexión de Loyverse desde el frontend.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoyverseConnectionSerializer
    
    def get_queryset(self):
        """Filtra conexiones para que cada usuario solo vea la suya."""
        return LoyverseUserConnection.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Obtiene la conexión del usuario actual o devuelve 404."""
        queryset = self.get_queryset()
        try:
            return queryset.get()
        except LoyverseUserConnection.DoesNotExist:
            return None
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Devuelve el estado de la conexión Loyverse del usuario.
        
        Si no existe conexión, devuelve información para conectar.
        """
        connection = self.get_object()
        
        if not connection:
            return Response({
                'is_connected': False,
                'connect_url': '/loyverse/connect/', 
                'message': 'No tienes conexión con Loyverse. Puedes conectar tu cuenta.'
            })
        
        serializer = self.get_serializer(connection)
        data = serializer.data
        data['is_connected'] = True
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def sync_prices(self, request):
        """
        Inicia la sincronización de precios con Loyverse.
        
        Opciones:
        - check_only: Solo verificar diferencias
        - force_lower_price: Actualizar incluso si precio local es menor
        - recalculate_first: Recalcular precios base primero
        """
        connection = self.get_object()
        
        if not connection:
            return Response(
                {'error': 'No tienes una conexión con Loyverse. Conecta tu cuenta primero.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not connection.is_active:
            return Response(
                {'error': 'Tu conexión con Loyverse no está activa. Por favor reconéctate.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si hay una sincronización en curso
        if connection.price_sync_status in ['SYNCING', 'QUEUED']:
            return Response(
                {'error': 'Ya hay una sincronización en curso. Por favor espera a que termine.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar opciones de sincronización
        options_serializer = SyncOptionsSerializer(data=request.data)
        if not options_serializer.is_valid():
            return Response(
                options_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        options = options_serializer.validated_data
        task_ids = {}
        
        # Recalcular precios base si se solicita
        if options.get('recalculate_first', False):
            recalculate_task = recalculate_user_base_prices_task.delay(request.user.id)
            task_ids['recalculate'] = recalculate_task.id
        
        # Iniciar sincronización con Loyverse
        sync_task = sync_user_prices_to_loyverse.delay(
            connection.id,
            check_only=options.get('check_only', False),
            force_lower_price=options.get('force_lower_price', False)
        )
        task_ids['sync'] = sync_task.id
        
        # Actualizar conexión para mostrar que está en cola
        connection.price_sync_status = 'QUEUED'
        connection.save(update_fields=['price_sync_status'])
        
        response_data = {
            'success': True,
            'message': 'Sincronización iniciada correctamente',
            'options': options,
            'task_ids': task_ids
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def sync_options(self, request):
        """Devuelve las opciones disponibles para la sincronización de precios."""
        options = {
            'check_only': {
                'label': 'Solo verificar diferencias',
                'help_text': 'No realizará cambios reales en Loyverse, solo mostrará las diferencias de precios.',
                'default': False
            },
            'force_lower_price': {
                'label': 'Forzar precios menores',
                'help_text': 'Actualizar productos en Loyverse incluso si el precio local es menor que el actual en Loyverse.',
                'default': False
            },
            'recalculate_first': {
                'label': 'Recalcular precios base primero',
                'help_text': 'Actualiza los precios base de todos tus productos usando tu tasa de cambio actual antes de sincronizar con Loyverse.',
                'default': False
            }
        }
        
        return Response(options)
    
    @action(detail=False, methods=['get'])
    def connection_url(self, request):
        """Devuelve la URL para conectar con Loyverse."""
        return Response({
            'connect_url': '/loyverse/connect/'
        })


@api_view(['GET'])
def check_loyverse_connection(request):
    """
    Endpoint para verificar si el usuario tiene una conexión activa con Loyverse.
    
    Si no tiene conexión o está inactiva, devuelve la URL para conectar.
    Este endpoint es utilizado por el frontend para redirigir al usuario
    al flujo de OAuth2 si es necesario.
    """
    if not request.user.is_authenticated:
        return Response({
            'error': 'Usuario no autenticado',
            'login_required': True
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        connection = LoyverseUserConnection.objects.get(user=request.user)
        
        if connection.is_active:
            # El usuario tiene una conexión activa
            return Response({
                'loyverse_connection_required': False,
                'is_active': True,
                'account_name': connection.loyverse_account_name,
                'email': connection.loyverse_email
            })
        else:
            # El usuario tiene una conexión pero no está activa
            return Response({
                'loyverse_connection_required': True,
                'is_active': False,
                'message': 'Tu conexión con Loyverse no está activa',
                'loyverse_connect_url': reverse('loyverse_integration:connect_loyverse')
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    except LoyverseUserConnection.DoesNotExist:
        # El usuario no tiene conexión con Loyverse
        return Response({
            'loyverse_connection_required': True,
            'is_active': False,
            'message': 'Necesitas conectar tu cuenta con Loyverse',
            'loyverse_connect_url': reverse('loyverse_integration:connect_loyverse')
        }, status=status.HTTP_401_UNAUTHORIZED)
