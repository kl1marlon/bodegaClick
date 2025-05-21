from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest
import os
import secrets
import urllib.parse
from .models import LoyverseUserConnection
import logging

# Importar helper functions y constantes
from .views_helpers import (
    loyverse_callback_handler,
    LOYVERSE_AUTHORIZATION_URL,
    LOYVERSE_TOKEN_URL,
    LOYVERSE_JWKS_URL,
    LOYVERSE_ISSUER
)

logger = logging.getLogger(__name__)

@login_required
def connect_loyverse_view(request: HttpRequest):
    """
    Redirige al usuario a Loyverse para autorizar la conexión de la aplicación.
    
    Acepta un parámetro 'next' en la URL para redirigir al usuario después de la conexión.
    """
    try:
        # Guardar la URL de redirección después de la conexión, si se proporciona
        next_url = request.GET.get('next')
        if next_url:
            request.session['loyverse_next_url'] = next_url
            
        client_id = os.environ.get('LOYVERSE_APP_CLIENT_ID')
        if not client_id:
            # Considerar loggear este error y mostrar una página de error más amigable
            return render(request, 'error_page.html', {'message': 'LOYVERSE_APP_CLIENT_ID no está configurado.'}, status=500)

        # Construir la REDIRECT_URI de forma absoluta
        # En producción, usamos una URL fija para evitar problemas de redirect_uri_mismatch
        # En desarrollo, construimos la URL dinámicamente
        if os.environ.get('DJANGO_ENVIRONMENT') == 'production':
            # URL fija para producción - DEBE coincidir EXACTAMENTE con la configurada en Loyverse Developer Dashboard
            production_domain = os.environ.get('PRODUCTION_DOMAIN', 'bodegaclick.onrender.com')
            redirect_uri = f"https://{production_domain}/loyverse/callback/"
        else:
            # Construcción dinámica para desarrollo
            redirect_uri_path = reverse('loyverse_integration:loyverse_callback')
            redirect_uri = request.build_absolute_uri(redirect_uri_path)

        scopes = "OPENID ITEMS_READ ITEMS_WRITE" # Ajusta los scopes según sea necesario
        state = secrets.token_urlsafe(32) # Generar un estado CSRF robusto
        request.session['loyverse_oauth_state'] = state
        request.session['loyverse_redirect_uri'] = redirect_uri # Guardar para usar en el callback

        params = {
            'client_id': client_id,
            'response_type': 'code',
            'scope': scopes,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        authorization_url = f"{LOYVERSE_AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

        return HttpResponseRedirect(authorization_url)
    except Exception as e:
        # Loggear la excepción e
        # Considerar mostrar una página de error genérica
        # logger.error(f"Error en connect_loyverse_view: {e}", exc_info=True)
        return render(request, 'error_page.html', {'message': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


def loyverse_callback_view(request: HttpRequest):
    """
    Maneja el callback de Loyverse después de la autorización del usuario.
    Intercambia el código de autorización por un token de acceso y un id_token.
    Decodifica el id_token para obtener información del usuario y guarda la conexión.
    """
    # Utilizar el handler reutilizable
    result = loyverse_callback_handler(request, for_registration=False)
    
    # Si el resultado es una conexión (no una respuesta HTTP de error)
    if not isinstance(result, HttpResponseRedirect) and not hasattr(result, 'status_code'):
        # La conexión fue creada exitosamente
        connection = result
        
        # Guardar en la sesión que la conexión fue exitosa
        request.session['loyverse_connection_success'] = True
        
        # Redirigir a la página principal o al dashboard de sincronización
        next_url = request.session.pop('loyverse_next_url', None)
        if next_url:
            return redirect(next_url)
        else:
            return redirect('loyverse_integration:sync_dashboard')
    else:
        # Si hubo un error, el handler ya devolvió una respuesta HTTP
        return result


@login_required
def sync_dashboard(request):
    """
    Vista para el panel de control de sincronización de precios con Loyverse.
    Muestra el estado de la conexión y opciones para iniciar la sincronización.
    """
    try:
        connection = LoyverseUserConnection.objects.get(user=request.user)
        context = {
            'loyverse_connected': connection.is_active,
            'connection': connection,
            'sync_status': connection.price_sync_status,
            'last_sync_details': connection.last_price_sync_details,
            'last_sync_time': connection.last_price_sync_end_time,
        }
    except LoyverseUserConnection.DoesNotExist:
        context = {
            'loyverse_connected': False,
            'connection_url': reverse('loyverse_integration:connect_loyverse'),
        }
    
    return render(request, 'loyverse_integration/sync_dashboard.html', context)


@login_required
def start_price_sync(request):
    """
    Vista para iniciar la sincronización de precios con Loyverse.
    Acepta parámetros para configurar el tipo de sincronización.
    """
    if request.method != 'POST':
        return render(request, 'error_page.html', {
            'message': 'Esta URL solo acepta solicitudes POST.'
        }, status=405)
    
    # Obtener parámetros de la solicitud
    check_only = request.POST.get('check_only', 'false').lower() == 'true'
    force_lower_price = request.POST.get('force_lower_price', 'false').lower() == 'true'
    recalculate_first = request.POST.get('recalculate_first', 'false').lower() == 'true'
    
    try:
        connection = LoyverseUserConnection.objects.get(user=request.user)
        
        if not connection.is_active:
            return render(request, 'loyverse_integration/sync_result.html', {
                'success': False,
                'message': 'La conexión con Loyverse no está activa. Por favor reconecta tu cuenta.'
            })
        
        # Verificar si hay una sincronización en curso
        if connection.price_sync_status == LoyverseUserConnection.SyncStatus.SYNCING or \
           connection.price_sync_status == LoyverseUserConnection.SyncStatus.QUEUED:
            return render(request, 'loyverse_integration/sync_result.html', {
                'success': False,
                'message': 'Ya hay una sincronización en curso. Por favor espera a que termine.'
            })
        
        from .tasks import recalculate_user_base_prices_task, sync_user_prices_to_loyverse
        
        task_ids = {}
        
        # Paso 1: Recalcular precios base si se solicita
        if recalculate_first:
            recalculate_task = recalculate_user_base_prices_task.delay(request.user.id)
            task_ids['recalculate'] = recalculate_task.id
            
        # Paso 2: Iniciar sincronización con Loyverse
        sync_task = sync_user_prices_to_loyverse.delay(
            connection.id,
            check_only=check_only,
            force_lower_price=force_lower_price
        )
        task_ids['sync'] = sync_task.id
        
        return render(request, 'loyverse_integration/sync_result.html', {
            'success': True,
            'message': 'Sincronización iniciada correctamente. La operación puede tardar varios minutos.',
            'recalculate_first': recalculate_first,
            'check_only': check_only,
            'task_ids': task_ids
        })
        
    except LoyverseUserConnection.DoesNotExist:
        return render(request, 'loyverse_integration/sync_result.html', {
            'success': False,
            'message': 'No tienes una conexión con Loyverse configurada. Por favor conecta tu cuenta primero.'
        })
    except Exception as e:
        logger.error(f"Error al iniciar sincronización para usuario {request.user.id}: {e}", exc_info=True)
        return render(request, 'loyverse_integration/sync_result.html', {
            'success': False,
            'message': f'Error al iniciar la sincronización: {str(e)}'
        })
