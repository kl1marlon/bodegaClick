"""
Decoradores para verificar la conexión Loyverse.

Estos decoradores permiten verificar que un usuario tiene una conexión
activa con Loyverse antes de acceder a ciertas vistas.
"""

from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse

def loyverse_connection_required(view_func):
    """
    Decorador que verifica que el usuario tiene una conexión activa con Loyverse.
    
    Si el usuario no tiene una conexión activa, se le redirige al flujo de OAuth2.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Si el usuario no está autenticado, redirigir al login
            return redirect('login')
        
        # Verificar si el usuario tiene una conexión Loyverse activa
        try:
            loyverse_connection = request.user.loyverse_connection
            if not loyverse_connection.is_active:
                # Si la conexión existe pero no está activa, redirigir a reconectar
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Para solicitudes AJAX, devolver un error 401
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
                return JsonResponse({
                    'error': 'No hay conexión con Loyverse',
                    'redirect_url': reverse('loyverse_integration:connect_loyverse')
                }, status=401)
            else:
                # Para solicitudes normales, redirigir
                messages.warning(request, 'Necesitas conectar tu cuenta con Loyverse para continuar.')
                return redirect('loyverse_integration:connect_loyverse')
        
        # Si todo está bien, ejecutar la vista original
        return view_func(request, *args, **kwargs)
    
    return wrapper
