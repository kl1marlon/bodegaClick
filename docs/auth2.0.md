# Documentación de Avances en Autenticación OAuth 2.0

Este documento servirá como bitácora y guía de trabajo para todos los avances, pruebas y configuraciones relacionados con la autenticación OAuth 2.0 en la integración de Loyverse con BodegaClick.

---

## Estructura de Tareas

### Tarea 1: Autenticación y OAuth 2.0
**Objetivo:** Lograr que el flujo de autenticación OAuth 2.0 con Loyverse funcione correctamente en el backend de BodegaClick.

#### Subtareas:
1. Configuración de variables de entorno para OAuth (client_id, client_secret, redirect_uri, etc).
2. Configuración de dominios y orígenes confiables en Django (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, etc).
3. Implementación y revisión de endpoints `/loyverse/connect/` y `/loyverse/callback/`.
4. Pruebas manuales del flujo de autorización y almacenamiento de tokens.
5. Pruebas del refresco de tokens.
6. Documentación de problemas, errores y soluciones encontradas.
7. Validación final en entorno de producción.

### Tarea 2: Sincronización y Celery
**Objetivo:** Una vez el flujo de autenticación funcione, proceder con la implementación y pruebas de las tareas de sincronización de precios (usando Celery).

---

## Bitácora de Avances y Pruebas

### [Fecha: 2025-05-11]

#### 1. Configuración Inicial y Variables de Entorno
- Se identificó la necesidad de definir correctamente las variables de entorno para OAuth:
    - `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` obtenidos del dashboard de Loyverse.
    - `COOLIFY_DOMAIN` definido únicamente con el dominio público del backend (ejemplo: `https://api.bodegaclick.coolify.app`).
    - (Opcional) `DJANGO_ALLOWED_HOSTS` para restringir hosts permitidos.
- Se configuró la Redirect URI en el dashboard de Loyverse como: `https://<dominio-backend>/loyverse/callback/`.

#### 2. Configuración de Django para despliegue
- Se añadió `COOLIFY_DOMAIN` a `CSRF_TRUSTED_ORIGINS` en settings.py para evitar problemas de CSRF.
- Se añadió la configuración `SECURE_PROXY_SSL_HEADER` y `USE_X_FORWARDED_HOST` para soportar HTTPS detrás de proxy en Coolify.
- Se comentó la recomendación de restringir `ALLOWED_HOSTS` para producción.

#### 3. Implementación de Endpoints OAuth
- Se revisó la vista `connect_loyverse_view`, que construye la redirect_uri usando `request.build_absolute_uri(reverse('loyverse_integration:loyverse_callback'))`.
- Se verificó que la callback esté correctamente definida y registrada en urls.py.

#### 4. Primeras pruebas del flujo
- Se intentó acceder a `/loyverse/connect/` sin estar autenticado.
- Django redirigió a `/accounts/login/` porque la vista requiere autenticación (`@login_required`).
- Se detectó que `/accounts/login/` no existe en las urls, resultando en un error 404.
- Se recomendó iniciar sesión primero en `/admin/` con un superusuario para establecer sesión y luego reintentar `/loyverse/connect/`.
- Se documentó cómo crear o cambiar la clave de superusuario usando `python manage.py createsuperuser` o `changepassword` en el terminal del contenedor de Coolify.

#### 5. Consideraciones de HTTP vs HTTPS
- Se recomendó usar siempre `https://<dominio-backend>` para evitar problemas de cookies y redirecciones inseguras.
- Se verificó que la configuración de proxy en Django permita la generación de URLs correctas con HTTPS.

#### 6. División de tareas y enfoque
- Se decidió dividir el trabajo en dos grandes tareas: (1) autenticación/OAuth y (2) sincronización/Celery.
- Se creó este documento para documentar cada avance, error y solución antes de pasar a la siguiente fase.

---

### [Fecha: 2025-05-11 - Actualización]  

#### 7. Corrección de Error en Referencias a SyncStatusChoices
- Se identificó un error al guardar o actualizar instancias de `LoyverseUserConnection` después del callback de OAuth2:
  ```
  TypeError: type object 'LoyverseUserConnection' has no attribute 'SyncStatusChoices'
  ```
- **Problema**: El código intentaba acceder a `LoyverseUserConnection.SyncStatusChoices.IDLE` pero la clase de choices estaba definida como `SyncStatus` en el modelo.
- **Solución**: Se corrigió la referencia en `views.py` cambiando `LoyverseUserConnection.SyncStatusChoices.IDLE` por `LoyverseUserConnection.SyncStatus.IDLE`.
- Se verificó que todas las demás referencias a los estados de sincronización usaran la clase correcta.

#### 8. Mejoras en la Lógica de Refresco de Token (Tarea 2.4)
- Se implementaron las siguientes mejoras en el modelo `LoyverseUserConnection`:

  1. **Nuevo método `test_token_validity()`**:
     - Realiza una petición a la API de Loyverse para verificar si el token sigue siendo válido.
     - Utiliza el endpoint `/merchants/me` por ser ligero y requerir autenticación.
     - Maneja diferentes códigos de estado HTTP para determinar la validez del token.
     - Incluye timeout de 5 segundos para evitar bloqueos.

  2. **Mejoras en `get_valid_access_token()`**:
     - Ahora verifica la validez del token incluso si no ha expirado según el tiempo.
     - Si el token falla la prueba de validez, intenta refrescarlo automáticamente.
     - Mejor documentación con docstrings detallados.

  3. **Mejoras en `refresh_access_token()`**:
     - Añadido timeout de 10 segundos para evitar bloqueos en la petición.
     - Manejo específico para errores de timeout.
     - Ampliado el reconocimiento de errores para incluir `invalid_token` además de `invalid_grant`.
     - Mejor documentación con docstrings detallados.

  4. **Mejoras en `record_sync_attempt()`**:
     - Uso correcto de las constantes de clase `SyncStatus` en lugar de strings literales.
     - Optimización al guardar solo los campos modificados con `update_fields`.
     - Mejor documentación con docstrings detallados.

#### 9. Pruebas de Conexión Exitosas
- Se realizaron pruebas de conexión con Loyverse y se logró establecer la conexión correctamente.
- Los tokens se almacenan cifrados en la base de datos usando `django-cryptography`.
- El panel de administración muestra correctamente el estado de las conexiones y los tokens.

## Notas y Observaciones
- Todas las configuraciones, errores y soluciones relacionados con autenticación se documentarán aquí antes de pasar a la siguiente fase.
- Se recomienda mantener este documento actualizado en cada cambio relevante.
- Se prioriza dejar el flujo de autenticación completamente funcional antes de avanzar con la lógica de sincronización de precios.

---

## Próximos Pasos
- ✅ Probar el flujo completo de `/loyverse/connect/` tras iniciar sesión en `/admin/`.
- ✅ Documentar errores y soluciones aplicadas.
- ✅ Validar almacenamiento correcto de tokens.
- ✅ Implementar y mejorar la lógica de refresco automático de tokens.
- 🔄 Configurar Celery y Redis para tareas asíncronas (Fase 3).
- 🔄 Implementar tareas de sincronización de precios.
- 🔄 Crear interfaz de usuario para gestionar la conexión y sincronización.
