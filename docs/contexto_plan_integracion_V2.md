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

**[EN PROGRESO - Depurando `redirect_uri`] Tarea B.1: Definir y Configurar URLs para OAuth**
*   **Estado:** Vistas y URLs base definidas. Error de `redirect_uri mismatch` siendo depurado.
*   **Acción:**
    1.  Asegurar que `loyverse_integration/urls.py` (con `connect_loyverse` y `loyverse_callback`) esté correctamente incluido en `config/urls.py` (el `urls.py` principal del proyecto).
    2.  **Verificar/Corregir `LOYVERSE_REDIRECT_URI`:** La `redirect_uri` configurada en el Developer Dashboard de Loyverse debe coincidir EXACTAMENTE con la URL absoluta generada por `request.build_absolute_uri(reverse('loyverse:loyverse_callback'))` cuando se accede desde el entorno de prueba de Render (HTTPS).
*   **Instrucción al Editor IA:** "Revisa la configuración de URLs. Ayúdame a asegurar que la `REDIRECT_URI` usada en la vista `connect_loyverse_view` y la configurada en Loyverse para el entorno de Render (`https://<tu-app>.onrender.com/loyverse/callback/`) coincidan perfectamente, incluyendo el protocolo HTTPS."

**[EN PROGRESO - Depurando `redirect_uri`] Tarea B.2: Implementar Vista `connect_loyverse_view`**
*   **Estado:** Implementada, pero el flujo se interrumpe por el error de `redirect_uri`.
*   **Acción:** Verificar que use `@login_required`, obtenga `LOYVERSE_APP_CLIENT_ID` de ENV, construya correctamente la `REDIRECT_URI` absoluta, defina `SCOPES`, genere y guarde `state` en sesión.
*   **Instrucción al Editor IA:** "Confirma que la vista `connect_loyverse_view` esté construyendo la `redirect_uri` de forma absoluta y correcta para el entorno de Render."

**[EN PROGRESO - Se llega aquí después del error de `redirect_uri`] Tarea B.3: Implementar Vista `loyverse_callback_view`**
*   **Estado:** Implementada, pero el error anterior (`redirect_uri mismatch`) impide probarla completamente. El error `TypeError: type object 'LoyverseUserConnection' has no attribute 'SyncStatusChoices'` fue identificado y la solución es usar las constantes de estado (ej. `LoyverseUserConnection.STATUS_IDLE`).
*   **Acción:**
    1.  Verificar `state`.
    2.  Intercambiar `code` por tokens.
    3.  **Implementar correctamente la decodificación y VALIDACIÓN del `id_token` JWT (incluyendo obtención de JWKS, verificación de firma, `audience` e `issuer`).**
    4.  Usar `LoyverseUserConnection.objects.update_or_create(user=request.user, defaults={...})` para guardar/actualizar la conexión. Asegurar que se asignen los estados correctamente usando las constantes del modelo.
*   **Instrucción al Editor IA:** "Una vez resuelto el problema de `redirect_uri`, revisa `loyverse_callback_view`. Asegúrate de que:
    *   La validación y decodificación del `id_token` JWT es completa y segura (obtención de claves de JWKS, verificación de firma, `aud`, `iss`).
    *   Los estados de `price_sync_status` se asignan usando las constantes definidas en el modelo (ej. `LoyverseUserConnection.STATUS_IDLE`) para evitar el `TypeError` anterior."

**[COMPLETADA - Lógica mejorada] Tarea B.4: Implementar y Probar Métodos de Refresco de Token**
*   **Estado:** Completada. Métodos `refresh_access_token()`, `get_valid_access_token()`, y `test_token_validity()` en `LoyverseUserConnection` fueron implementados y mejorados.
*   **Prueba Pendiente:** Probar exhaustivamente en el entorno de Render una vez que el flujo OAuth2 completo funcione.

---

## Fase C: Tarea Celery para Sincronización de Precios con Loyverse

**Objetivo:** Adaptar el script de sincronización de precios existente para que funcione como una tarea Celery por usuario, utilizando su token OAuth2.

**[PENDIENTE] Tarea C.1: Crear Tarea Celery `sync_user_prices_to_loyverse`**
*   **Acción:** En `loyverse_integration/tasks.py`, crear `@shared_task(...) sync_user_prices_to_loyverse(loyverse_connection_id, check_only=False, force_lower_price=False)`.
*   **Lógica Principal:**
    1.  Obtener `LoyverseUserConnection` y `access_token` válido.
    2.  Actualizar estado a `SYNCING`.
    3.  Obtener productos locales del usuario (filtrados por `loyverse_connection.user` de la tabla `facturacion.Producto`).
    4.  Obtener todos los items de la cuenta Loyverse del usuario.
    5.  Bucle de comparación y actualización (adaptado de `scripts/sync_all_loyverse_prices.py`):
        *   Usar `producto_local.precio_base` (que ya debería estar actualizado y redondeado por un proceso previo del usuario en BodegaClick).
        *   **Implementar `time.sleep(1.05)` antes de cada POST a Loyverse.**
        *   **Manejar HTTP 429 con reintentos y backoff.**
    6.  Actualizar estado final y `last_price_sync_details`.
*   **Instrucción al Editor IA:** "Crea la tarea Celery `sync_user_prices_to_loyverse` en `loyverse_integration/tasks.py` siguiendo la lógica detallada en `CONTEXTO_GLOBAL_Y_PLAN_V3.md` y reutilizando/adaptando el script `sync_all_loyverse_prices.py` proporcionado anteriormente."

**[PENDIENTE] Tarea C.2: (Opcional, pero Recomendado) Tarea Celery `recalculate_user_base_prices_task`**
*   **Descripción:** Tarea para recalcular `precio_base` en `facturacion.Producto` para un `user_id` dado, usando sus `TasaCambio` y `precio_base_usd`, aplicando redondeo.
*   **Instrucción al Editor IA:** "Define la tarea Celery `recalculate_user_base_prices_task`."

---

## Fase D: Interfaz de Usuario y Endpoints

**Objetivo:** Permitir a los usuarios gestionar su conexión e iniciar sincronizaciones.

**[PENDIENTE] Tarea D.1: Vista y URL para Iniciar Sincronización con Loyverse**
*   **Acción:** Crear `trigger_loyverse_price_sync_view` y su URL.
*   **Instrucción al Editor IA:** "Implementa la vista y URL para `trigger_loyverse_price_sync_view`."

**[PENDIENTE] Tarea D.2: (Si se implementa C.2) Endpoint API y/o Vista para Recalcular Precios Base Locales del Usuario**
*   **Acción:** Crear un endpoint o vista que encole `recalculate_user_base_prices_task`.
*   **Instrucción al Editor IA:** "Define un endpoint API o una vista para iniciar `recalculate_user_base_prices_task`."

**[PENDIENTE] Tarea D.3: Mostrar Estado al Usuario (Frontend/Plantillas)**
*   **Acción:** Diseñar cómo el frontend de React (o plantillas Django) mostrará el estado de la conexión y sincronización, y cómo el usuario interactuará con estos flujos.
*   **Instrucción al Editor IA:** "Proporciona ejemplos o ideas sobre cómo el frontend podría interactuar con estos nuevos flujos y mostrar la información de estado."

---

## Fase E: Pruebas Finales, Refinamiento y Despliegue en Render

*   Pruebas E2E.
*   Revisión de logs en Render.
*   Ajustes de configuración de Celery workers en Render si es necesario.