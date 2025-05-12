from django.contrib.auth import get_user_model
from loyverse_integration.models import LoyverseUserConnection # Asegúrate que la app se llame así
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# === PASO CRUCIAL: USA UN USERNAME VÁLIDO ===
# Reemplaza 'admin_bodegaclick' con el username REAL del usuario
# para el cual ya existe una LoyverseUserConnection.
# Puedes encontrar los usernames en tu admin de Django.
try:
    # Intenta con el username que usaste para conectar con Loyverse
    usuario_bodegaclick = User.objects.get(username='admin_bodegaclick') # O el email, o el id si lo conoces
    print(f"Usuario de BodegaClick encontrado: {usuario_bodegaclick.username}")
except User.DoesNotExist:
    print("Error: El usuario de BodegaClick especificado NO existe en la base de datos.")
    print("Por favor, verifica el username o crea/conecta el usuario primero.")
    # Aquí deberías salir o intentar con otro usuario si este falla.
    exit() # Salir del shell si no se encuentra el usuario para no continuar con errores.

# === Ahora intenta obtener la conexión ===
try:
    connection = LoyverseUserConnection.objects.get(user=usuario_bodegaclick)
    print(f"Conexión Loyverse encontrada para {usuario_bodegaclick.username} (ID: {connection.id})")
except LoyverseUserConnection.DoesNotExist:
    print(f"Error: No se encontró una LoyverseUserConnection para el usuario {usuario_bodegaclick.username}.")
    print("Asegúrate de que este usuario haya completado el flujo OAuth2 con Loyverse.")
    exit() # Salir si no hay conexión

# Si llegamos aquí, 'connection' existe.
print(f"  Token actual expira en: {connection.expires_at}")
print(f"  Está activo: {connection.is_active}")
old_access_token_encrypted = connection.access_token # Guardar el token cifrado para comparar luego
old_expires_at = connection.expires_at

# Forzar la expiración del token (para la prueba de refresco)
print("\nForzando expiración del token...")
connection.expires_at = timezone.now() - timedelta(minutes=30) # Asegurar que esté bien expirado
connection.save()
connection.refresh_from_db() # Recargar desde BD para confirmar el cambio
print(f"  Token forzado a expirar en (desde BD): {connection.expires_at}")

# Intentar obtener un token válido (esto debería disparar el refresco)
print("\nIntentando obtener token válido (esto debería invocar refresh_access_token())...")
# El método get_valid_access_token() debe devolver el token desencriptado
valid_token_desencriptado = connection.get_valid_access_token()

# Volver a cargar la conexión desde la BD para ver los cambios guardados por refresh_access_token
connection.refresh_from_db()

if valid_token_desencriptado:
    print(f"  ¡Refresco Exitoso!")
    print(f"  Nuevo access_token (primeros 20 chars desencriptado): {valid_token_desencriptado[:20]}...")
    if connection.access_token == old_access_token_encrypted:
        print("  ADVERTENCIA: El access_token encriptado en la BD NO cambió después del refresco. Verifica la lógica de guardado en refresh_access_token.")
    else:
        print("  CONFIRMADO: El access_token encriptado en la BD SÍ cambió.")
else:
    print("  FALLÓ el refresco o la obtención del token.")

print(f"  Nuevo expires_at en BD: {connection.expires_at}")
print(f"  Debería ser mayor que el 'old_expires_at': {old_expires_at}")
print(f"  Último error (si hubo): {connection.last_error_message}")
print(f"  Conexión está activa: {connection.is_active}")

# Prueba de validez (opcional, si implementaste test_token_validity)
# print("\nProbando validez del nuevo token contra la API de Loyverse...")
# is_valid_now = connection.test_token_validity()
# print(f"  El nuevo token es actualmente válido según la API de Loyverse: {is_valid_now}")
# print(f"  Mensaje de error de validación (si hubo): {connection.last_error_message}") # test_token_validity puede actualizar esto