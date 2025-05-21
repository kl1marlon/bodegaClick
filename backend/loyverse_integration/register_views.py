"""
Vistas para el flujo de registro con Loyverse.

Este archivo implementa las vistas necesarias para que los usuarios
puedan registrarse en BodegaClick comenzando con autenticación en Loyverse.
"""

import os
import secrets
import urllib.parse
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken

from .models import LoyverseUserConnection
from .views import (
    LOYVERSE_AUTHORIZATION_URL,
    LOYVERSE_TOKEN_URL,
    LOYVERSE_JWKS_URL,
    LOYVERSE_ISSUER
)

User = get_user_model()
logger = logging.getLogger(__name__)

def register_with_loyverse(request):
    """
    Inicia el flujo de registro conectando primero con Loyverse.
    
    Esta vista no requiere autenticación previa, a diferencia de connect_loyverse_view.
    """
    try:
        # Establecer el modo de registro en la sesión
        request.session['loyverse_registration_mode'] = True
        
        client_id = os.environ.get('LOYVERSE_APP_CLIENT_ID')
        if not client_id:
            return render(request, 'error_page.html', 
                         {'message': 'LOYVERSE_APP_CLIENT_ID no está configurado.'}, 
                         status=500)

        # Construir la REDIRECT_URI de forma absoluta
        # En producción, usamos una URL fija para evitar problemas de redirect_uri_mismatch
        if os.environ.get('DJANGO_ENVIRONMENT') == 'production':
            production_domain = os.environ.get('PRODUCTION_DOMAIN', 'bodegaclick.onrender.com')
            redirect_uri = f"https://{production_domain}/loyverse/register-callback/"
        else:
            # Construcción dinámica para desarrollo
            redirect_uri_path = reverse('loyverse_integration:loyverse_register_callback')
            redirect_uri = request.build_absolute_uri(redirect_uri_path)

        scopes = "OPENID ITEMS_READ ITEMS_WRITE"
        state = secrets.token_urlsafe(32)
        request.session['loyverse_oauth_state'] = state
        request.session['loyverse_redirect_uri'] = redirect_uri

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
        logger.error(f"Error en register_with_loyverse: {e}", exc_info=True)
        return render(request, 'error_page.html', 
                     {'message': f'Ocurrió un error inesperado: {str(e)}'}, 
                     status=500)


@csrf_protect
def loyverse_register_callback(request):
    """
    Maneja el callback de Loyverse durante el proceso de registro.
    
    Esta vista recibe la información de Loyverse y muestra un formulario
    para completar el registro con contraseña y otros datos necesarios.
    """
    from .views import loyverse_callback_handler
    
    # Verificar si es un modo de registro desde la sesión
    is_registration = request.session.get('loyverse_registration_mode', False)
    
    if not is_registration:
        messages.error(request, "Flujo de registro inválido. Por favor, inténtalo de nuevo.")
        return redirect('inicio')  # Redirigir a la página principal
    
    # Procesar la respuesta de Loyverse
    result = loyverse_callback_handler(request, for_registration=True)
    
    if isinstance(result, dict) and result.get('success'):
        # Si el procesamiento fue exitoso, extraer los datos de Loyverse
        loyverse_data = result.get('loyverse_data', {})
        
        # Renderizar formulario para completar el registro
        return render(request, 'loyverse_integration/complete_registration.html', {
            'loyverse_data': loyverse_data,
            'loyverse_user_subject': loyverse_data.get('loyverse_user_subject'),
            'loyverse_account_name': loyverse_data.get('loyverse_account_name'),
            'loyverse_email': loyverse_data.get('loyverse_email'),
        })
    else:
        # Si hubo un error, result ya es una respuesta HTTP
        return result


@csrf_protect
def complete_registration(request):
    """
    Completa el registro del usuario después de la autenticación con Loyverse.
    
    Esta vista recibe el formulario con la contraseña y otros datos,
    crea el usuario y su conexión Loyverse, y lo autentica.
    """
    if request.method != 'POST':
        return redirect('loyverse_integration:register_with_loyverse')
    
    # Verificar si tenemos la información necesaria en la sesión
    loyverse_user_subject = request.session.get('loyverse_user_subject')
    access_token = request.session.get('loyverse_access_token')
    refresh_token = request.session.get('loyverse_refresh_token')
    expires_at = request.session.get('loyverse_expires_at')
    token_type = request.session.get('loyverse_token_type')
    scope = request.session.get('loyverse_scope')
    loyverse_account_name = request.session.get('loyverse_account_name')
    loyverse_email = request.session.get('loyverse_email')
    
    # Validar datos esenciales
    if not loyverse_user_subject or not access_token or not expires_at:
        messages.error(request, "Información incompleta para completar el registro. Por favor, inténtalo de nuevo.")
        return redirect('loyverse_integration:register_with_loyverse')
    
    # Obtener y validar datos del formulario
    username = request.POST.get('username')
    email = request.POST.get('email') or loyverse_email  # Usar email de Loyverse si no se proporciona
    password = request.POST.get('password')
    password_confirm = request.POST.get('password_confirm')
    business_name = request.POST.get('business_name') or loyverse_account_name  # Usar nombre de cuenta si no se proporciona
    
    # Validaciones
    errors = {}
    
    if not username:
        errors['username'] = 'El nombre de usuario es obligatorio'
    elif len(username) < 3:
        errors['username'] = 'El nombre de usuario debe tener al menos 3 caracteres'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Este nombre de usuario ya está en uso'
    
    if not email:
        errors['email'] = 'El email es obligatorio'
    elif User.objects.filter(email=email).exists():
        errors['email'] = 'Este email ya está registrado'
    
    if not password:
        errors['password'] = 'La contraseña es obligatoria'
    elif len(password) < 8:
        errors['password'] = 'La contraseña debe tener al menos 8 caracteres'
    
    if password != password_confirm:
        errors['password_confirm'] = 'Las contraseñas no coinciden'
    
    if not business_name:
        errors['business_name'] = 'El nombre del negocio es obligatorio'
    
    # Si hay errores, volver al formulario
    if errors:
        return render(request, 'loyverse_integration/complete_registration.html', {
            'errors': errors,
            'loyverse_user_subject': loyverse_user_subject,
            'loyverse_account_name': loyverse_account_name,
            'loyverse_email': loyverse_email,
            'username': username,
            'email': email,
            'business_name': business_name,
        })
    
    try:
        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', '')
        )
        
        # Configurar información de perfil si existe
        if hasattr(user, 'profile'):
            user.profile.business_name = business_name
            user.profile.save()
        
        # Crear la conexión con Loyverse
        from django.utils import timezone
        
        LoyverseUserConnection.objects.create(
            user=user,
            loyverse_user_subject=loyverse_user_subject,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type or 'Bearer',
            expires_at=expires_at,
            scope=scope,
            loyverse_account_name=loyverse_account_name,
            loyverse_email=loyverse_email,
            is_active=True,
            last_token_refresh_time=timezone.now(),
            price_sync_status=LoyverseUserConnection.SyncStatus.IDLE
        )
        
        # Iniciar sesión automáticamente
        login(request, user)
        
        # Limpiar la sesión
        for key in ['loyverse_registration_mode', 'loyverse_user_subject', 'loyverse_access_token', 
                   'loyverse_refresh_token', 'loyverse_expires_at', 'loyverse_token_type', 
                   'loyverse_scope', 'loyverse_account_name', 'loyverse_email']:
            if key in request.session:
                del request.session[key]
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        messages.success(request, f"¡Bienvenido, {username}! Tu cuenta ha sido creada y conectada con Loyverse.")
        
        # Redirigir al dashboard o página principal
        return redirect('loyverse_integration:sync_dashboard')
        
    except Exception as e:
        logger.error(f"Error al completar el registro: {e}", exc_info=True)
        messages.error(request, f"Error al crear tu cuenta: {str(e)}")
        return redirect('loyverse_integration:register_with_loyverse')
