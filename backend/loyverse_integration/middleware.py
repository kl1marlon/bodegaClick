"""
Middleware para verificar la conexión Loyverse de los usuarios.

Este middleware verifica que los usuarios autenticados tengan una conexión
activa con Loyverse. Si no la tienen, los redirige al flujo de OAuth2.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

# Rutas que están exentas de la verificación de conexión Loyverse
EXEMPT_PATHS = [
    '/admin/',
    '/loyverse/connect/',
    '/loyverse/callback/',
    '/health/',
    '/api/token/',
    '/api/token/refresh/',
    '/api/register/',
]

class LoyverseConnectionMiddleware:
    """
    Middleware que verifica que los usuarios autenticados tengan una conexión
    activa con Loyverse. Si no la tienen, los redirige al flujo de OAuth2.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar la solicitud solo si el usuario está autenticado
        if request.user.is_authenticated:
            # No verificar en rutas exentas
            path = request.path
            if not any(path.startswith(exempt_path) for exempt_path in EXEMPT_PATHS):
                # Verificar si el usuario tiene una conexión Loyverse activa
                try:
                    loyverse_connection = request.user.loyverse_connection
                    if not loyverse_connection.is_active:
                        # Si la conexión existe pero no está activa, redirigir a reconectar
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            # Para solicitudes AJAX, devolver un error 401
                            from django.http import JsonResponse
                            return JsonResponse({
                                'error': 'Conexión con Loyverse inactiva',
                                'redirect_url': reverse('loyverse_integration:connect_loyverse')
                            }, status=401)
                        else:
                            # Para solicitudes normales, redirigir
                            messages.warning(request, 'Tu conexión con Loyverse no está activa. Por favor, reconéctate.')
                            return redirect('loyverse_integration:connect_loyverse')
                except AttributeError:
                    # Si el usuario no tiene conexión Loyverse, redirigir a conectar
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        # Para solicitudes AJAX, devolver un error 401
                        from django.http import JsonResponse
                        return JsonResponse({
                            'error': 'No hay conexión con Loyverse',
                            'redirect_url': reverse('loyverse_integration:connect_loyverse')
                        }, status=401)
                    else:
                        # Para solicitudes normales, redirigir
                        messages.warning(request, 'Necesitas conectar tu cuenta con Loyverse para continuar.')
                        return redirect('loyverse_integration:connect_loyverse')
        
        # Continuar con el flujo normal
        response = self.get_response(request)
        return response
