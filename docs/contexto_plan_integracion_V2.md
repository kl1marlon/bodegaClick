# Contexto Global y Plan de Desarrollo V3: Módulo de Integración con Loyverse en BodegaClick

## Sección 1: Contexto General del Proyecto BodegaClick

### 1.1. Stack Tecnológico Principal:
*   **Backend:** Django 4.2.0, Django REST Framework 3.14.0
*   **Procesamiento Asíncrono:** Celery 5.4.0 con Redis 5.2.1 como broker/backend. (Configurado en `settings.py`)
*   **Servidor Web Backend:** Gunicorn 21.2.0
*   **Base de Datos:** PostgreSQL 13.
*   **Autenticación Django:** Se utiliza el sistema de usuarios de Django (`django.contrib.auth.models.User`).
*   **App Existente Principal:** `facturacion` (contiene modelos `Producto`, `Factura`, `DetalleFactura`, `TasaCambio`, `Webhook` - todos estos son específicos para cada usuario de BodegaClick).
*   **Cifrado de Campos:** Se utiliza `django-cryptography` para cifrar datos sensibles en la base de datos. La clave `DJANGO_FIELD_ENCRYPTION_KEY` se gestiona vía variables de entorno.
*   **Contenerización y Despliegue:** Docker, Docker Compose, y despliegue en Render (previamente Coolify/Railway). Las variables de entorno se gestionan en la plataforma de despliegue y localmente con `.env`.

### 1.2. Objetivo del Módulo de Integración con Loyverse:
Crear una nueva app de Django llamada `loyverse_integration` para permitir que cada usuario de BodegaClick conecte **UNA ÚNICA cuenta de Loyverse** propia. Las funcionalidades principales son:
1.  Establecer una conexión segura y persistente usando **OAuth 2.0**.
2.  Permitir la **sincronización de precios de productos** desde BodegaClick hacia la cuenta Loyverse conectada del usuario, de forma asíncrona usando Celery.
3.  (Opcional a futuro) Permitir "Login con Loyverse" (Social Login vía OpenID Connect).

### 1.3. Autenticación con Loyverse (OAuth 2.0):
*   BodegaClick actúa como cliente OAuth2, usando un `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` globales para la aplicación BodegaClick (configurados vía ENV VARS).
*   Cada `LoyverseUserConnection` (ver Sección 1.5) almacenará `access_token`, `refresh_token`, y `expires_at` específicos del usuario y su cuenta Loyverse.
*   Los tokens se almacenarán cifrados usando `django-cryptography`.
*   Scopes iniciales requeridos: `OPENID`, `ITEMS_READ`, `ITEMS_WRITE`.
*   Se extraerá información del `id_token` JWT (como `sub`, `name`, `email`) para poblar el modelo `LoyverseUserConnection`.

### 1.4. Multi-Tenancy de Datos en BodegaClick:
*   **Cada usuario de BodegaClick tiene sus propios datos aislados.**
*   Los modelos `Producto`, `Factura`, `DetalleFactura`, y `TasaCambio` (dentro de la app `facturacion`) **DEBEN ESTAR ASOCIADOS a un `User` específico de BodegaClick** mediante un campo `ForeignKey`. (Esta modificación a los modelos de `facturacion` es una tarea pendiente o en progreso).

### 1.5. Flujo de Datos de Precios y Modelo `LoyverseUserConnection`:
*   **Flujo Lógico de Precios:**
    1.  Usuario define `precio_base_usd` para sus productos en BodegaClick.
    2.  Usuario define sus `TasaCambio` (BCV, Paralelo) en BodegaClick.
    3.  BodegaClick calcula `precio_base = precio_base_usd * tasa_seleccionada_por_usuario` (con lógica de redondeo especial).
    4.  Este `precio_base` se sincroniza con `default_price` en Loyverse.
*   **Modelo `loyverse_integration.LoyverseUserConnection`:**
    *   `user`: `OneToOneField` a `settings.AUTH_USER_MODEL`.
    *   `access_token`: `encrypt(models.TextField())`.
    *   `refresh_token`: `encrypt(models.TextField())`.
    *   `expires_at`: `DateTimeField`.
    *   `scope`: `TextField`.
    *   `loyverse_user_subject`: `CharField(unique=True)` (ID del usuario en Loyverse).
    *   `loyverse_account_name`, `loyverse_email`: Para info de OpenID.
    *   `is_active`: `BooleanField`.
    *   `last_error_message`: `TextField`.
    *   Campos de estado de sincronización de precios: `price_sync_status` (CharField con `choices` y constantes de estado definidas en el modelo), `last_price_sync_start_time`, `last_price_sync_end_time`, `last_price_sync_details` (JSONField).
    *   Métodos implementados/mejorados: `is_access_token_expired()`, `refresh_access_token()`, `get_valid_access_token()`, `test_token_validity()`, `record_sync_attempt()`.

### 1.6. Límite de Tasa API Loyverse:
*   **1 petición por segundo por token de cuenta (por `LoyverseUserConnection`).**
*   Se gestionará con `time.sleep(1.05)` dentro de las tareas Celery antes de cada llamada POST/PUT a Loyverse y con manejo de errores HTTP 429.

---

## Sección 2: Plan de Desarrollo Detallado y Estado Actual

### Fase 1: Configuración Inicial, Modelos de Datos y Cifrado

**Objetivo:** Establecer la app `loyverse_integration`, definir modelos para conexiones de usuario, implementar cifrado, y adaptar modelos de `facturacion` para multi-tenancy.

**[COMPLETADA] Tarea A.1: Crear Nueva App de Django `loyverse_integration`**
*   **Estado:** Completada. La app `loyverse_integration` existe en `backend/` y está en `INSTALLED_APPS`.

**[COMPLETADA] Tarea A.2: Instalar y Configurar `django-cryptography`**
*   **Estado:** Completada. `django-cryptography` instalado, configurado con `DJANGO_FIELD_ENCRYPTION_KEY` vía `.env`.

**[COMPLETADA - Decisión: Usar ENV VARS] Tarea A.3: Estrategia para `LoyverseAppCredential`**
*   **Estado:** Completada. Se decidió acceder a `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` directamente desde variables de entorno.

**[COMPLETADA] Tarea A.4: Definir Modelo `LoyverseUserConnection`**
*   **Estado:** Completada. El modelo está definido en `loyverse_integration/models.py` con campos cifrados y de estado, usando `OneToOneField` a `User`.

**[EN PROGRESO / PENDIENTE DE REVISIÓN] Tarea A.5: Modificar Modelos de `facturacion` para Multi-Tenancy**
*   **Acción Pendiente:** Confirmar que los modelos `Producto`, `Factura`, y `TasaCambio` en `facturacion/models.py` tengan correctamente añadido el campo `user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='...')`.
*   **Instrucción al Editor IA:** "Verifica que los modelos `Producto`, `Factura`, y `TasaCambio` en la app `facturacion` incluyan una `ForeignKey` a `settings.AUTH_USER_MODEL`. Si no, añádela. Considera las implicaciones para `makemigrations` si hay datos existentes."

**[PENDIENTE - Depende de A.5] Tarea A.6: Crear y Aplicar Migraciones Combinadas**
*   **Acción:** Una vez confirmada la Tarea A.5:
    ```bash
    python manage.py makemigrations facturacion loyverse_integration
    python manage.py migrate
    ```
*   **Instrucción al Editor IA:** "Una vez que los modelos de `facturacion` estén actualizados para multi-tenancy, genera los comandos para crear y aplicar las migraciones para AMBAS apps (`facturacion` y `loyverse_integration`)."

**[PENDIENTE] Tarea A.7: Registrar Modelo `LoyverseUserConnection` en Admin**
*   **Acción:** En `loyverse_integration/admin.py`, registrar `LoyverseUserConnection` con `list_display` útiles.
*   **Instrucción al Editor IA:** "Implementa el registro del modelo `LoyverseUserConnection` en `loyverse_integration/admin.py`."

---

### Fase B: Implementación y Prueba del Flujo OAuth 2.0

**Objetivo:** Permitir a un usuario de BodegaClick (ya existente en el sistema) conectar su única cuenta Loyverse y gestionar los tokens.

**[COMPLETADA] Tarea B.1: Definir y Configurar URLs para OAuth**
*   **Estado:** Completada. URLs configuradas correctamente y problema de `redirect_uri mismatch` resuelto.
*   **Solución:**
    1.  Se verificó que `loyverse_integration/urls.py` (con `connect_loyverse` y `loyverse_callback`) está correctamente incluido en `config/urls.py` con el namespace `loyverse_integration`.
    2.  **Corregido `LOYVERSE_REDIRECT_URI`:** Se implementó una solución que usa URLs fijas en producción para garantizar que coincidan exactamente con las configuradas en el Developer Dashboard de Loyverse.
    3.  Se añadieron logs para depuración de la `redirect_uri` utilizada en el intercambio de tokens.

**[COMPLETADA] Tarea B.2: Implementar Vista `connect_loyverse_view`**
*   **Estado:** Completada y funcionando correctamente.
*   **Implementación:** La vista usa `@login_required`, obtiene `LOYVERSE_APP_CLIENT_ID` de ENV, construye correctamente la `REDIRECT_URI` absoluta (ahora con soporte para URLs fijas en producción), define `SCOPES`, genera y guarda `state` en sesión.
*   **Mejoras:** Se modificó la construcción de la `redirect_uri` para usar una URL fija en producción que coincide exactamente con la configurada en Loyverse.

**[COMPLETADA] Tarea B.3: Implementar Vista `loyverse_callback_view`**
*   **Estado:** Completada y funcionando correctamente. Se ha probado el flujo completo con éxito.
*   **Implementación:**
    1.  Verificación de `state` funcionando correctamente.
    2.  Intercambio de `code` por tokens implementado y probado.
    3.  **Decodificación y VALIDACIÓN del `id_token` JWT implementada correctamente**, incluyendo obtención de JWKS, verificación de firma, `audience` e `issuer`.
    4.  Uso de `LoyverseUserConnection.objects.update_or_create(user=request.user, defaults={...})` para guardar/actualizar la conexión, con estados asignados correctamente usando las constantes del modelo.
*   **Mejoras:** Se añadieron logs adicionales para depuración de la `redirect_uri` utilizada en el intercambio de tokens.

**[COMPLETADA - Lógica mejorada] Tarea B.4: Implementar y Probar Métodos de Refresco de Token**
*   **Estado:** Completada. Métodos `refresh_access_token()`, `get_valid_access_token()`, y `test_token_validity()` en `LoyverseUserConnection` fueron implementados y mejorados.
*   **Prueba Pendiente:** Probar exhaustivamente en el entorno de Render una vez que el flujo OAuth2 completo funcione.

---

## Fase C: Tarea Celery para Sincronización de Precios con Loyverse

**Objetivo:** Adaptar el script de sincronización de precios existente para que funcione como una tarea Celery por usuario, utilizando su token OAuth2.

**[COMPLETADA] Tarea C.1: Crear Tarea Celery `sync_user_prices_to_loyverse`**
*   **Estado:** Completada. La tarea Celery `sync_user_prices_to_loyverse` ha sido implementada en `loyverse_integration/tasks.py`.
*   **Características implementadas:**
    1.  Obtiene `LoyverseUserConnection` y `access_token` válido.
    2.  Actualiza estado a `SYNCING` y registra el inicio de la sincronización.
    3.  Obtiene productos locales del usuario específico (filtrados por `loyverse_connection.user`).
    4.  Obtiene todos los items de la cuenta Loyverse del usuario mediante paginación.
    5.  Implementa un bucle de comparación y actualización con:
        *   Uso de `producto_local.precio_base` para sincronizar con Loyverse.
        *   Pausa de 0.5-1 segundo entre peticiones para respetar el límite de la API.
        *   Manejo de errores HTTP y reintentos.
    6.  Actualiza estado final y `last_price_sync_details` con estadísticas detalladas.
*   **Opciones soportadas:** `check_only` (solo verificación) y `force_lower_price` (forzar actualización incluso si el precio local es menor).

**[COMPLETADA] Tarea C.2: Tarea Celery `recalculate_user_base_prices_task`**
*   **Estado:** Completada. La tarea `recalculate_user_base_prices_task` ha sido implementada.
*   **Características:**
    *   Recalcula `precio_base` en `facturacion.Producto` para un `user_id` específico.
    *   Utiliza las tasas de cambio del usuario (BCV o PARALELO según configuración).
    *   Aplica la lógica de redondeo especial para precios en bolívares.
    *   Genera un resumen detallado de la operación con productos actualizados y sin cambios.

---

## Fase D: Interfaz de Usuario y Endpoints

**Objetivo:** Permitir a los usuarios gestionar su conexión e iniciar sincronizaciones.

**[COMPLETADA] Tarea D.1: Vista y URL para Panel de Control e Iniciar Sincronización con Loyverse**
*   **Estado:** Completada. Se han implementado dos vistas principales:
    *   `sync_dashboard`: Panel de control que muestra el estado de la conexión y opciones de sincronización.
    *   `start_price_sync`: Endpoint para iniciar la sincronización con opciones configurables.
*   **URLs configuradas:**
    *   `/loyverse/dashboard/`: Acceso al panel de control de sincronización.
    *   `/loyverse/start-sync/`: Endpoint para iniciar la sincronización.

**[COMPLETADA] Tarea D.2: Integración del Recálculo de Precios en el Flujo de Sincronización**
*   **Estado:** Completada. La vista `start_price_sync` permite opcionalmente ejecutar `recalculate_user_base_prices_task` antes de la sincronización.
*   **Características:**
    *   Opción `recalculate_first` que permite al usuario recalcular sus precios base antes de sincronizar.
    *   Verificación de estado para evitar sincronizaciones simultáneas.
    *   Manejo de errores y feedback al usuario.

**[COMPLETADA] Tarea D.3: Mostrar Estado al Usuario (Plantillas Django)**
*   **Estado:** Completada. Se han implementado plantillas Django para mostrar el estado de la conexión y sincronización.
*   **Plantillas implementadas:**
    *   `sync_dashboard.html`: Panel de control completo que muestra:
        *   Estado de la conexión con Loyverse (activa/inactiva)
        *   Información de la cuenta conectada (nombre, email)
        *   Estado del token OAuth (válido/expirado)
        *   Estado de la última sincronización con estadísticas detalladas
        *   Formulario para iniciar una nueva sincronización con opciones configurables
    *   `sync_result.html`: Página de resultado que muestra:
        *   Confirmación de inicio de sincronización
        *   Detalles de la operación iniciada
        *   Mensajes de error en caso de problemas

---

## Fase E: Pruebas Finales, Refinamiento y Despliegue en Render

**Objetivo:** Verificar el funcionamiento completo del sistema en entorno de producción y realizar ajustes finales.

**[PENDIENTE] Tarea E.1: Pruebas End-to-End del Flujo Completo**
*   **Acciones:**
    *   Probar el flujo completo de conexión OAuth2 con Loyverse en entorno de producción.
    *   Verificar la sincronización de precios con cuentas reales.
    *   Comprobar el correcto funcionamiento del multi-tenancy con múltiples usuarios.

**[PENDIENTE] Tarea E.2: Monitoreo y Optimización**
*   **Acciones:**
    *   Revisar logs detallados en Render/Coolify.
    *   Optimizar la configuración de Celery workers según la carga observada.
    *   Implementar alertas para errores críticos en la sincronización.

**[PENDIENTE] Tarea E.3: Documentación para Usuarios Finales**
*   **Acciones:**
    *   Crear guía de usuario para el proceso de conexión con Loyverse.
    *   Documentar el proceso de sincronización de precios y sus opciones.
    *   Añadir sección de preguntas frecuentes y solución de problemas.

---

## Fase F: Integración API REST para Frontend

**Objetivo:** Implementar endpoints API REST para permitir que el frontend React interactue con la funcionalidad de sincronización de Loyverse.

**[COMPLETADA] Tarea F.1: Implementar Serializers**
*   **Estado:** Completada. Se han creado serializers para la conexión Loyverse y las opciones de sincronización.
*   **Archivos implementados:**
    *   `serializers.py` con `LoyverseConnectionSerializer` y `SyncOptionsSerializer`.
    *   El serializer de conexión oculta datos sensibles como tokens y expone solo información necesaria para el frontend.

**[COMPLETADA] Tarea F.2: Implementar ViewSets y Endpoints API**
*   **Estado:** Completada. Se ha creado un ViewSet con múltiples endpoints para todas las operaciones necesarias.
*   **Endpoints implementados:**
    *   `GET /loyverse/api/connections/status/`: Devuelve el estado de conexión del usuario.
    *   `POST /loyverse/api/connections/sync_prices/`: Inicia la sincronización con opciones configurables.
    *   `GET /loyverse/api/connections/sync_options/`: Devuelve las opciones disponibles para sincronización.
    *   `GET /loyverse/api/connections/connection_url/`: Devuelve la URL para conectar con Loyverse.
*   **Seguridad:** Se aplica `IsAuthenticated` para garantizar que un usuario solo puede acceder a su propia conexión.

**[COMPLETADA] Tarea F.3: Configuración de URLs**
*   **Estado:** Completada. Se han configurado las URLs para los endpoints API utilizando DefaultRouter.
*   **Características:**
    *   Las rutas API están bajo el namespace `loyverse_integration`.
    *   Se mantienen las URLs anteriores para vistas de Django regulares.

**[EN CURSO] Tarea F.4: Pruebas de Endpoints API**
*   **Estado:** En curso. Se ha verificado el funcionamiento del endpoint `status`, faltan probar los demás endpoints.
*   **Acciones pendientes:**
    *   Probar el endpoint `sync_prices` con Postman/cURL.
    *   Verificar respuestas de error y manejo de casos especiales.
    *   Realizar pruebas con múltiples usuarios para confirmar aislamiento de datos.