from django.db import models
from django.conf import settings
from django.utils import timezone
from django_cryptography.fields import encrypt
from datetime import timedelta
import os
import requests
import logging

try:
    from .views import LOYVERSE_TOKEN_URL
except ImportError:
    LOYVERSE_TOKEN_URL = "https://api.loyverse.com/oauth/token"

logger = logging.getLogger(__name__)

class LoyverseUserConnection(models.Model):
    class SyncStatus(models.TextChoices):
        IDLE = 'IDLE', 'Idle'
        QUEUED = 'QUEUED', 'Queued'
        SYNCING = 'SYNCING', 'Syncing'
        COMPLETED = 'COMPLETED', 'Completed'
        COMPLETED_WITH_ERRORS = 'COMPLETED_WITH_ERRORS', 'Completed with Errors'
        FAILED = 'FAILED', 'Failed'
        TOKEN_INVALID = 'TOKEN_INVALID', 'Token Invalid'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyverse_connection',
        verbose_name="Usuario de BodegaClick"
    )
    loyverse_user_subject = models.CharField(max_length=255, unique=True, help_text="Identificador 'sub' único del usuario en Loyverse.", verbose_name="Subject ID de Loyverse")
    loyverse_account_name = models.CharField(max_length=255, blank=True, null=True, help_text="Nombre del negocio en Loyverse (claim 'name').", verbose_name="Nombre de Cuenta Loyverse")
    loyverse_email = models.EmailField(blank=True, null=True, help_text="Email de la cuenta Loyverse (claim 'email').", verbose_name="Email Loyverse")

    access_token = encrypt(models.TextField(verbose_name="Token de Acceso Loyverse (cifrado)"))
    refresh_token = encrypt(models.TextField(blank=True, null=True, verbose_name="Token de Refresco Loyverse (cifrado)"))
    token_type = models.CharField(max_length=50, default="Bearer", verbose_name="Tipo de Token")
    expires_at = models.DateTimeField(help_text="Fecha y hora de expiración del access_token.", verbose_name="Fecha de Expiración del Token")
    scope = models.TextField(help_text="Scopes concedidos por el usuario, separados por espacio.", verbose_name="Alcance (Scopes)")

    is_active = models.BooleanField(
        default=False,
        help_text="Indica si la conexión y los tokens son actualmente válidos y utilizables.",
        verbose_name="Conexión Activa"
    )
    last_token_refresh_time = models.DateTimeField(null=True, blank=True, verbose_name="Última Actualización de Token")
    last_error_message = models.TextField(blank=True, null=True, verbose_name="Último Mensaje de Error")

    price_sync_status = models.CharField(
        max_length=30,
        choices=SyncStatus.choices,
        default=SyncStatus.IDLE,
        help_text="Estado de la última sincronización de precios",
        verbose_name="Estado de Sincronización de Precios"
    )
    last_price_sync_start_time = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Última Sinc. Precios")
    last_price_sync_end_time = models.DateTimeField(null=True, blank=True, verbose_name="Fin Última Sinc. Precios")
    last_price_sync_details = models.JSONField(null=True, blank=True, help_text="Resumen o detalles de la última sincronización (ej. productos actualizados/fallidos).", verbose_name="Detalles Última Sinc. Precios")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    def __str__(self):
        user_display = self.user.username if self.user else "Usuario Desconocido"
        account_display = self.loyverse_account_name or 'Sin Nombre de Cuenta'
        return f"Conexión Loyverse para {user_display} ({account_display})"

    def is_access_token_expired(self):
        """Verifica si el token de acceso ha expirado, con un margen de 5 minutos."""
        if not self.expires_at:
            return True # Si no hay fecha de expiración, asumir expirado o no válido
        return timezone.now() >= self.expires_at - timedelta(minutes=5)

    def get_valid_access_token(self):
        """Devuelve un access_token válido, refrescándolo si es necesario y posible.
        
        Returns:
            str: El token de acceso válido, o None si no se pudo obtener o refrescar.
        """
        if not self.is_active:
            logger.warning(f"Intento de obtener token para conexión inactiva: user {self.user_id}")
            return None

        if self.is_access_token_expired():
            logger.info(f"Token expirado para user {self.user_id}. Intentando refrescar.")
            if not self.refresh_access_token(): # refresh_access_token devuelve True en éxito, False en fallo
                logger.error(f"Fallo al refrescar token para user {self.user_id}. La conexión podría estar inactiva.")
                return None # Opcionalmente, podrías lanzar una excepción específica aquí
        elif not self.test_token_validity():
            # Si el token no ha expirado según el tiempo pero ya no es válido
            logger.warning(f"Token aparentemente válido para user {self.user_id} falló en prueba de validez. Intentando refrescar.")
            if not self.refresh_access_token():
                logger.error(f"Fallo al refrescar token para user {self.user_id} después de fallar prueba de validez.")
                return None
        
        # Asegurarse de que el token no esté encriptado directamente aquí, ya que el campo es un EncryptedTextField.
        # La desencriptación ocurre cuando accedes al atributo del modelo.
        return self.access_token # Devuelve el valor desencriptado

    def refresh_access_token(self):
        """Refresca el token de acceso usando el refresh_token. 
        
        Returns:
            bool: True si el refresco fue exitoso, False si falló.
        """
        if not self.refresh_token:
            logger.error(f"No hay refresh token para user {self.user_id}. No se puede refrescar.")
            self.deactivate_connection(error_message="No hay refresh token disponible.")
            return False

        client_id = os.environ.get('LOYVERSE_APP_CLIENT_ID')
        client_secret = os.environ.get('LOYVERSE_APP_CLIENT_SECRET')

        if not client_id or not client_secret:
            logger.error(f"LOYVERSE_APP_CLIENT_ID o LOYVERSE_APP_CLIENT_SECRET no configurados. User: {self.user_id}")
            self.last_error_message = "Credenciales de aplicación no configuradas en el servidor."
            self.save(update_fields=['last_error_message'])
            return False

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token, # Django-cryptography desencripta al acceder
            'client_id': client_id,
            'client_secret': client_secret,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(LOYVERSE_TOKEN_URL, data=payload, headers=headers, timeout=10)  # Añadido timeout
            response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
            token_data = response.json()

            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token') # Loyverse puede o no devolver un nuevo refresh token
            expires_in = token_data.get('expires_in')
            scope = token_data.get('scope', self.scope) # Mantener scope anterior si no se devuelve
            token_type = token_data.get('token_type', self.token_type)

            if not new_access_token or expires_in is None:
                logger.error(f"Respuesta de refresco de token incompleta para user {self.user_id}: {token_data}")
                self.last_error_message = "Respuesta de refresco de token de Loyverse incompleta."
                # Considerar si desactivar la conexión aquí o permitir reintentos
                self.save(update_fields=['last_error_message'])
                return False
            
            self.update_tokens(
                access_token=new_access_token,
                refresh_token=new_refresh_token if new_refresh_token else self.refresh_token, # Usar el nuevo si existe
                expires_in_seconds=int(expires_in),
                scope=scope,
                token_type=token_type
            )
            logger.info(f"Token refrescado exitosamente para user {self.user_id}")
            return True

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP refrescando token para user {self.user_id}: {e}. Respuesta: {e.response.text if e.response else 'N/A'}", exc_info=True)
            error_response_data = {}
            if e.response is not None:
                try:
                    error_response_data = e.response.json()
                except ValueError: # No es JSON
                    error_response_data = {'raw_response': e.response.text}
            
            error_code = error_response_data.get('error')
            error_description = error_response_data.get('error_description', str(e))
            self.last_error_message = f"Error al refrescar token: {error_code} - {error_description}"

            # Si el refresh token es inválido, desactivar la conexión
            if e.response is not None and e.response.status_code in [400, 401] and error_code in ['invalid_grant', 'invalid_token']:
                logger.warning(f"Refresh token inválido para user {self.user_id}. Desactivando conexión.")
                self.deactivate_connection(error_message=f"El token de refresco es inválido o ha sido revocado: {error_description}")
            else:
                self.save(update_fields=['last_error_message'])
            return False
        except requests.exceptions.Timeout:
            logger.error(f"Timeout refrescando token para user {self.user_id}")
            self.last_error_message = "Timeout al intentar refrescar el token. El servidor de Loyverse no respondió a tiempo."
            self.save(update_fields=['last_error_message'])
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red refrescando token para user {self.user_id}: {e}", exc_info=True)
            self.last_error_message = f"Error de red al intentar refrescar el token: {e}"
            self.save(update_fields=['last_error_message'])
            return False
        except Exception as e:
            logger.error(f"Error inesperado refrescando token para user {self.user_id}: {e}", exc_info=True)
            self.last_error_message = f"Error inesperado durante el refresco del token: {str(e)}"
            self.save(update_fields=['last_error_message'])
            return False

    def update_tokens(self, access_token, refresh_token, expires_in_seconds, scope, token_type="Bearer"):
        """Actualiza los tokens y la fecha de expiración."""
        self.access_token = access_token
        if refresh_token: # El refresh token no siempre se devuelve
            self.refresh_token = refresh_token
        self.expires_at = timezone.now() + timedelta(seconds=expires_in_seconds)
        self.scope = scope
        self.token_type = token_type
        self.is_active = True
        self.last_token_refresh_time = timezone.now()
        self.last_error_message = None # Limpiar errores previos al refrescar token
        self.save()

    def deactivate_connection(self, error_message="Desactivada por el usuario."):
        """Desactiva la conexión, por ejemplo, si el usuario revoca el acceso."""
        self.is_active = False
        self.last_error_message = error_message
        # Opcionalmente, podrías querer limpiar los tokens aquí por seguridad
        # self.access_token = ""
        # self.refresh_token = ""
        logger.info(f"Conexión Loyverse desactivada para user {self.user_id}. Razón: {error_message}")
        self.save(update_fields=['is_active', 'last_error_message'])

    def test_token_validity(self):
        """Prueba si el token de acceso actual es válido haciendo una petición a la API de Loyverse.
        
        Returns:
            bool: True si el token es válido, False si no lo es.
        """
        if not self.is_active or not self.access_token:
            return False
            
        # Endpoint para probar el token - usamos un endpoint ligero como /merchants/me
        test_url = "https://api.loyverse.com/v1.0/merchants/me"
        headers = {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(test_url, headers=headers, timeout=5)
            # Si la respuesta es 200, el token es válido
            if response.status_code == 200:
                return True
                
            # Si es 401 o 403, el token no es válido
            if response.status_code in [401, 403]:
                logger.warning(f"Token inválido para user {self.user_id}. Status: {response.status_code}")
                return False
                
            # Otros códigos de estado podrían indicar problemas con la API, no necesariamente con el token
            logger.warning(f"Respuesta inesperada al probar token para user {self.user_id}. Status: {response.status_code}")
            return False
            
        except requests.exceptions.RequestException as e:
            # Error de red, no podemos determinar si el token es válido
            logger.warning(f"Error al probar validez del token para user {self.user_id}: {e}")
            # Asumimos que el token podría ser válido, el problema podría ser de red
            return True
            
    def record_sync_attempt(self, success, error_message=None, details=None):
        """Registra un intento de sincronización de precios.
        
        Args:
            success (bool): Si la sincronización fue exitosa.
            error_message (str, optional): Mensaje de error si la sincronización falló.
            details (dict, optional): Detalles adicionales sobre la sincronización.
        """
        if success:
            self.price_sync_status = self.SyncStatus.COMPLETED
            self.last_price_sync_end_time = timezone.now()
            self.last_error_message = None
            if details:
                self.last_price_sync_details = details
        else:
            self.price_sync_status = self.SyncStatus.FAILED
            self.last_error_message = error_message
            if details:
                self.last_price_sync_details = details
        self.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_error_message', 'last_price_sync_details'])

    class Meta:
        verbose_name = "Conexión de Usuario Loyverse"
        verbose_name_plural = "Conexiones de Usuarios Loyverse"
        ordering = ['-created_at']
