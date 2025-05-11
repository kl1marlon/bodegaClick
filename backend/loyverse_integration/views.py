from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest
import os
import secrets
import urllib.parse
import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from datetime import timedelta
from django.utils import timezone
from .models import LoyverseUserConnection
import logging

# Create your views here.

LOYVERSE_AUTHORIZATION_URL = "https://api.loyverse.com/oauth/authorize"
LOYVERSE_TOKEN_URL = "https://api.loyverse.com/oauth/token"
LOYVERSE_JWKS_URL = "https://api.loyverse.com/.well-known/jwks.json"
LOYVERSE_ISSUER = "https://api.loyverse.com"

logger = logging.getLogger(__name__)

@login_required
def connect_loyverse_view(request: HttpRequest):
    """
    Redirige al usuario a Loyverse para autorizar la conexión de la aplicación.
    """
    try:
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
    error_message = None
    code = request.GET.get('code')
    state_from_response = request.GET.get('state')
    state_from_session = request.session.pop('loyverse_oauth_state', None)
    stored_redirect_uri = request.session.pop('loyverse_redirect_uri', None)

    if not code:
        error_message = "No se recibió el código de autorización de Loyverse."
        logger.error(f"Loyverse callback error for user {request.user.id}: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=400)

    if not state_from_session or state_from_response != state_from_session:
        error_message = "Discrepancia en el estado CSRF. La solicitud podría estar comprometida."
        logger.error(f"Loyverse callback CSRF error for user {request.user.id}: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=400)
    
    if not stored_redirect_uri:
        # Esto no debería suceder si connect_loyverse_view lo guardó correctamente
        error_message = "No se encontró la URI de redirección original en la sesión."
        logger.error(f"Loyverse callback error for user {request.user.id}: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    client_id = os.environ.get('LOYVERSE_APP_CLIENT_ID')
    client_secret = os.environ.get('LOYVERSE_APP_CLIENT_SECRET')

    if not client_id or not client_secret:
        error_message = "Las credenciales de la aplicación Loyverse (ID o Secreto del Cliente) no están configuradas en el servidor."
        logger.error(f"Loyverse callback config error for user {request.user.id}: {error_message}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    token_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': stored_redirect_uri, # Usar la misma redirect_uri que en la solicitud de autorización
        'code': code,
        'grant_type': 'authorization_code',
    }
    
    # Log para depuración de redirect_uri
    logger.info(f"Usando redirect_uri para intercambio de token: {stored_redirect_uri}")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(LOYVERSE_TOKEN_URL, data=token_payload, headers=headers)
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx
        token_data = response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"Error al intercambiar el código por token con Loyverse: {e}. Respuesta: {e.response.text if e.response else 'N/A'}"
        logger.error(f"Loyverse token exchange error for user {request.user.id}: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    id_token_str = token_data.get('id_token')
    expires_in = token_data.get('expires_in')
    scope_from_response = token_data.get('scope')

    if not all([access_token, id_token_str, expires_in]):
        error_message = "La respuesta del token de Loyverse no contenía todos los campos esperados (access_token, id_token, expires_in)."
        logger.error(f"Loyverse token response incomplete for user {request.user.id}: {token_data}")
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
            raise jwt.exceptions.InvalidKeyError("No se encontró la clave pública correspondiente en JWKS para el id_token.")

        # Decodificar y verificar el id_token
        id_token_payload = jwt.decode(
            id_token_str,
            key=public_key,
            algorithms=['RS256'],
            audience=client_id,
            issuer=LOYVERSE_ISSUER
        )

    except jwt.PyJWTError as e:
        error_message = f"Error al decodificar o verificar el id_token de Loyverse: {e}"
        logger.error(f"Loyverse id_token decoding/verification error for user {request.user.id}: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)
    except requests.exceptions.RequestException as e:
        error_message = f"Error al obtener JWKS de Loyverse: {e}"
        logger.error(f"Loyverse JWKS fetch error for user {request.user.id}: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    loyverse_user_subject = id_token_payload.get('sub')
    loyverse_account_name = id_token_payload.get('name')
    loyverse_email = id_token_payload.get('email')
    # loyverse_merchant_id = id_token_payload.get('https://schemas.loyverse.com/merchant_id') # Ajusta si Loyverse proporciona esto en el id_token

    if not loyverse_user_subject:
        error_message = "El id_token de Loyverse no contiene el campo 'sub' (subject/user ID)."
        logger.error(f"Loyverse id_token missing 'sub' for user {request.user.id}: {id_token_payload}")
        return render(request, 'error_page.html', {'message': error_message}, status=500)

    expires_at = timezone.now() + timedelta(seconds=expires_in)

    try:
        connection, created = LoyverseUserConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'loyverse_user_subject': loyverse_user_subject,
                'access_token': access_token, # El modelo se encarga de cifrarlo
                'refresh_token': refresh_token, # El modelo se encarga de cifrarlo
                'expires_at': expires_at,
                'scope': scope_from_response,
                'loyverse_account_name': loyverse_account_name,
                'loyverse_email': loyverse_email,
                # 'loyverse_merchant_id': loyverse_merchant_id, # Si se obtiene
                'is_active': True,
                'last_error_message': None, # Limpiar errores previos
                'price_sync_status': LoyverseUserConnection.SyncStatus.IDLE, # Resetear estado de sync
            }
        )
        logger.info(f"Loyverse connection {'creada' if created else 'actualizada'} para el usuario {request.user.id} con Loyverse subject {loyverse_user_subject}")
        # Redirigir a una página de éxito, por ejemplo, el dashboard del usuario
        # return redirect('user_dashboard') # Ajusta el nombre de la URL de tu dashboard
        return render(request, 'loyverse_connection_success.html', {
            'message': f"¡Conexión con Loyverse establecida exitosamente para {loyverse_account_name or loyverse_email or 'tu cuenta'}!"
        })

    except Exception as e:
        error_message = f"Error al guardar la conexión de Loyverse en la base de datos: {e}"
        logger.error(f"Loyverse DB save error for user {request.user.id}: {error_message}", exc_info=True)
        return render(request, 'error_page.html', {'message': error_message}, status=500)
