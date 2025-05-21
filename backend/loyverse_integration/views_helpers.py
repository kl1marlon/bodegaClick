"""
Funciones auxiliares para vistas de integración con Loyverse.

Este archivo contiene funciones comunes utilizadas por las vistas
de conexión y registro con Loyverse.
"""

import os
import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from django.utils import timezone
import logging
from datetime import timedelta
from django.shortcuts import render

logger = logging.getLogger(__name__)

# URLs de Loyverse
LOYVERSE_AUTHORIZATION_URL = "https://api.loyverse.com/oauth/authorize"
LOYVERSE_TOKEN_URL = "https://api.loyverse.com/oauth/token"
LOYVERSE_JWKS_URL = "https://api.loyverse.com/.well-known/jwks.json"
LOYVERSE_ISSUER = "https://api.loyverse.com"

def loyverse_callback_handler(request, for_registration=False):
    """
    Procesa el callback de Loyverse tanto para conexión como para registro.
    
    Si for_registration=True, no requiere un usuario autenticado y
    devuelve los datos para completar el registro en lugar de crear la conexión.
    
    Args:
        request: La solicitud HTTP con código y estado de Loyverse
        for_registration: Si es True, procesa como parte de un registro nuevo
        
    Returns:
        - Para for_registration=True: Un dict con los datos de Loyverse o una respuesta HTTP con error
        - Para for_registration=False: Una conexión Loyverse o una respuesta HTTP con error
    """
    error_message = None
    code = request.GET.get('code')
    state_from_response = request.GET.get('state')
    state_from_session = request.session.pop('loyverse_oauth_state', None)
    stored_redirect_uri = request.session.pop('loyverse_redirect_uri', None)

    if not code:
        error_message = "No se recibió el código de autorización de Loyverse."
        logger.error(f"Loyverse callback error: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=400)

    if not state_from_session or state_from_response != state_from_session:
        error_message = "Discrepancia en el estado CSRF. La solicitud podría estar comprometida."
        logger.error(f"Loyverse callback CSRF error: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=400)
    
    if not stored_redirect_uri:
        error_message = "No se encontró la URI de redirección original en la sesión."
        logger.error(f"Loyverse callback error: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    client_id = os.environ.get('LOYVERSE_APP_CLIENT_ID')
    client_secret = os.environ.get('LOYVERSE_APP_CLIENT_SECRET')

    if not client_id or not client_secret:
        error_message = "Las credenciales de la aplicación Loyverse no están configuradas."
        logger.error(f"Loyverse callback config error: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    token_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': stored_redirect_uri,
        'code': code,
        'grant_type': 'authorization_code',
    }
    
    # Log para depuración de redirect_uri
    logger.info(f"Usando redirect_uri para intercambio de token: {stored_redirect_uri}")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(LOYVERSE_TOKEN_URL, data=token_payload, headers=headers)
        response.raise_for_status()
        token_data = response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"Error al intercambiar el código por token: {e}."
        logger.error(f"Loyverse token exchange error: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    id_token_str = token_data.get('id_token')
    expires_in = token_data.get('expires_in')
    scope_from_response = token_data.get('scope')

    if not all([access_token, id_token_str, expires_in]):
        error_message = "La respuesta del token de Loyverse no contenía todos los campos esperados."
        logger.error(f"Loyverse token response incomplete: {token_data}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    try:
        # Obtener las claves públicas JWKS de Loyverse
        jwks_response = requests.get(LOYVERSE_JWKS_URL)
        jwks_response.raise_for_status()
        jwks = jwks_response.json()

        # Decodificar la cabecera del id_token para obtener el 'kid'
        id_token_header = jwt.get_unverified_header(id_token_str)
        kid = id_token_header.get('kid')

        # Encontrar la clave pública correspondiente en JWKS
        public_key = None
        for key_dict in jwks.get('keys', []):
            if key_dict.get('kid') == kid:
                public_key = RSAAlgorithm.from_jwk(key_dict)
                break
        
        if not public_key:
            raise jwt.exceptions.InvalidKeyError("No se encontró la clave pública correspondiente en JWKS.")

        # Decodificar y verificar el id_token
        id_token_payload = jwt.decode(
            id_token_str,
            key=public_key,
            algorithms=['RS256'],
            audience=client_id,
            issuer=LOYVERSE_ISSUER
        )

    except jwt.PyJWTError as e:
        error_message = f"Error al decodificar o verificar el id_token: {e}"
        logger.error(f"Loyverse id_token verification error: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)
    except requests.exceptions.RequestException as e:
        error_message = f"Error al obtener JWKS de Loyverse: {e}"
        logger.error(f"Loyverse JWKS fetch error: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    loyverse_user_subject = id_token_payload.get('sub')
    loyverse_account_name = id_token_payload.get('name')
    loyverse_email = id_token_payload.get('email')

    if not loyverse_user_subject:
        error_message = "El id_token de Loyverse no contiene el campo 'sub' (subject/user ID)."
        logger.error(f"Loyverse id_token missing 'sub': {id_token_payload}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    expires_at = timezone.now() + timedelta(seconds=expires_in)
    
    # Si estamos en modo registro, guardar datos en la sesión y devolver información
    if for_registration:
        # Guardar información importante en la sesión
        request.session['loyverse_user_subject'] = loyverse_user_subject
        request.session['loyverse_access_token'] = access_token
        request.session['loyverse_refresh_token'] = refresh_token
        request.session['loyverse_expires_at'] = expires_at.isoformat()
        request.session['loyverse_token_type'] = token_data.get('token_type', 'Bearer')
        request.session['loyverse_scope'] = scope_from_response
        request.session['loyverse_account_name'] = loyverse_account_name
        request.session['loyverse_email'] = loyverse_email
        
        # Devolver datos para el formulario de registro
        return {
            'success': True,
            'loyverse_data': {
                'loyverse_user_subject': loyverse_user_subject,
                'loyverse_account_name': loyverse_account_name,
                'loyverse_email': loyverse_email,
            }
        }
    
    # Si es conexión normal, se requiere un usuario autenticado
    if not request.user.is_authenticated:
        error_message = "Debes iniciar sesión para conectar tu cuenta con Loyverse."
        logger.error(f"Loyverse connection attempt without authentication")
        return render(request, 'error_page.html', {'message': error_message}, status=401)
        
    # Para conexión regular, crear o actualizar la conexión
    from .models import LoyverseUserConnection
    
    try:
        connection, created = LoyverseUserConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'loyverse_user_subject': loyverse_user_subject,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': expires_at,
                'scope': scope_from_response,
                'loyverse_account_name': loyverse_account_name,
                'loyverse_email': loyverse_email,
                'last_error_message': None,
                'is_active': True,
                'last_token_refresh_time': timezone.now(),
                'price_sync_status': LoyverseUserConnection.SyncStatus.IDLE
            }
        )
        
        logger.info(f"Conexión Loyverse {'creada' if created else 'actualizada'} exitosamente para el usuario {request.user.username}")
        
        # Guardar en la sesión que la conexión fue exitosa
        request.session['loyverse_connection_success'] = True
        
        return connection
        
    except Exception as e:
        error_message = f"Error al guardar la conexión Loyverse: {e}"
        logger.error(f"Loyverse DB save error: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)
