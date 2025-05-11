# Plan de Desarrollo: Módulo de Integración con Loyverse para BodegaClick

Este plan detalla las fases y tareas para crear un módulo que permita a los usuarios de BodegaClick conectar sus cuentas de Loyverse mediante OAuth 2.0 y sincronizar datos, inicialmente precios.

**Editor de Código de IA, por favor sigue estas tareas paso a paso. Presta atención a los detalles de cada tarea y al archivo `CONTEXTO_PROYECTO.md` actualizado.**

---

## Fase 1: Configuración Inicial, Modelos de Datos y Cifrado

**Objetivo:** Establecer la nueva app `loyverse_integration`, definir los modelos para las credenciales de la app y las conexiones de usuario, e implementar el cifrado de datos sensibles.

**[COMPLETADA] Tarea 1.1: Crear Nueva App de Django `loyverse_integration`**
*   **Acción:**
    1.  En la raíz del proyecto Django, ejecutar: `python manage.py startapp loyverse_integration`
    2.  Añadir `'loyverse_integration'` a la lista `INSTALLED_APPS` en `config/settings.py`.
*   **Instrucción al Editor IA:** "Ejecuta los pasos para crear la app `loyverse_integration` y registrarla en `INSTALLED_APPS`."
*   **Nota:** La app `loyverse_integration` fue creada en el directorio `backend` y añadida a `INSTALLED_APPS` en `backend/config/settings.py`.

**[COMPLETADA] Tarea 1.2: Instalar y Configurar librería de Cifrado para Campos**
*   **Estado:** Completada
*   **Notas:**
    - Se decidió cambiar `django-fernet-fields` por `django-cryptography` debido a problemas de compatibilidad con Django 4.2.
    - `django-cryptography` ha sido instalado y añadido a `requirements.txt`.
    - Se generó clave de cifrado, se añadió a `.env` como `DJANGO_FIELD_ENCRYPTION_KEY`, y se configuró `FIELD_ENCRYPTION_KEYS` en `settings.py`.
    - Los modelos que usan campos cifrados fueron actualizados para usar `encrypt()` de `django-cryptography`.
*   **Acción:**
    1.  Añadir `django-cryptography` a `requirements.txt` y ejecutar `pip install django-cryptography`.
    2.  Generar una clave de cifrado:
        ```python
        # Desde una shell de Python:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        print(f"DJANGO_FIELD_ENCRYPTION_KEY={key}")
        ```
    3.  Añadir `DJANGO_FIELD_ENCRYPTION_KEY` como variable de entorno en el archivo `.env` y en la configuración del entorno de despliegue (Coolify).
    4.  Configurar `FIELD_ENCRYPTION_KEYS` en `config/settings.py`:
        ```python
        # config/settings.py
        import os
        FIELD_ENCRYPTION_KEYS = [os.environ.get('DJANGO_FIELD_ENCRYPTION_KEY')]
        ```
*   **Instrucción al Editor IA:** "Se guio en la instalación y configuración de `django-cryptography`, incluyendo la generación y el manejo seguro de la `DJANGO_FIELD_ENCRYPTION_KEY`. Se actualizaron los modelos para usar la nueva librería."

**[DECISIÓN TOMADA - USAR ENV VARS] Tarea 1.3: (Opcional, Decidir Estrategia) Definir Modelo `LoyverseAppCredential` o Usar ENV VARS Directamente**
*   **Discusión:** Las credenciales `client_id` y `client_secret` de BodegaClick son globales para la app. Pueden almacenarse como variables de entorno y accederse directamente, o mediante un modelo singleton. Usar ENV VARS es más simple si no cambian y no necesitas una UI para gestionarlas. **Para este plan, asumiremos acceso directo a ENV VARS para `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` para simplificar, eliminando la necesidad del modelo `LoyverseAppCredential`.**
*   **Acción (si se opta por modelo):** Definir el modelo en `loyverse_integration/models.py` (cifrando `client_secret`).
*   **Instrucción al Editor IA:** "Vamos a acceder a `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` directamente desde las variables de entorno en el código. No crearemos el modelo `LoyverseAppCredential` por ahora."
*   **Nota:** Se decidió usar variables de entorno directamente para `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET`.

**[COMPLETADA] Tarea 1.4: Definir Modelo `LoyverseUserConnection`**
*   **Estado:** Completada
*   **Acción:**
    1.  Crear/actualizar el archivo `loyverse_integration/models.py`.
    2.  Definir la clase `LoyverseUserConnection(models.Model)` con los campos especificados en el `contexto-integracion.md` y las adaptaciones para `django-cryptography` (usando `encrypt(models.TextField())` para `access_token` y `refresh_token`).
    3.  Incluir campos para:
        *   `user` (ForeignKey o OneToOneField a `settings.AUTH_USER_MODEL`)
        *   `access_token` (cifrado)
        *   `refresh_token` (cifrado, opcional)
        *   `expires_at` (DateTimeField para la expiración del token)
        *   `scope` (CharField o TextField para los permisos)
        *   `loyverse_user_subject` (CharField, identificador único del usuario en Loyverse)
        *   `loyverse_merchant_id` (CharField, opcional)
        *   `loyverse_account_name` (CharField, opcional)
        *   `loyverse_email` (EmailField, opcional)
        *   `is_active` (BooleanField)
        *   Campos de estado de sincronización (ej. `price_sync_status`, `last_price_sync_start_time`, etc., según la estructura proporcionada por el usuario).
        *   Campos de auditoría (`created_at`, `updated_at`).
*   **Instrucción al Editor IA:** "Define el modelo `LoyverseUserConnection` en `loyverse_integration/models.py` con los campos requeridos, asegurando que los tokens se almacenen cifrados usando `django-cryptography` y la estructura de campos proporcionada por el usuario."
*   **Nota:** Modelo definido y actualizado según la especificación del usuario, usando `django-cryptography`.

**[COMPLETADA] Tarea 1.5: Crear y Aplicar Migraciones Iniciales para `loyverse_integration`**
*   **Estado:** Completada
*   **Acción:**
    1.  Ejecutar `python manage.py makemigrations loyverse_integration`.
    2.  Ejecutar `python manage.py migrate loyverse_integration`.
*   **Instrucción al Editor IA:** "Genera y aplica las migraciones para la app `loyverse_integration`."
*   **Nota:** Migraciones creadas y aplicadas exitosamente después de resolver problemas con la librería de cifrado.

**Tarea 1.6: Registrar Modelo en el Admin de Django**
*   **Acción:** En `loyverse_integration/admin.py`, registrar `LoyverseUserConnection`.
    *   Configurar `list_display` para mostrar campos útiles como `user`, `loyverse_account_name`, `is_active`, `price_sync_status`, `expires_at`.
    *   Considerar `readonly_fields` para los tokens cifrados si se muestran (aunque generalmente no se muestran directamente).
*   **Instrucción al Editor IA:** "Escribe el código para `loyverse_integration/admin.py` para registrar el modelo `LoyverseUserConnection`, configurando `list_display` con `user`, `loyverse_account_name`, `is_active`, `price_sync_status`, y `updated_at`."

---

## Fase 2: Implementación del Flujo OAuth 2.0

**Objetivo:** Implementar la lógica para que los usuarios de BodegaClick conecten sus cuentas de Loyverse.

**Tarea 2.1: Definir URLs para el Flujo OAuth**
*   **Acción:**
    1.  Crear `loyverse_integration/urls.py`.
    2.  Definir rutas para `connect_loyverse` (inicia el flujo) y `loyverse_callback` (maneja la respuesta de Loyverse).
    3.  Incluir estas URLs en el `urls.py` principal del proyecto Django (bajo un namespace como `loyverse`).
*   **Instrucción al Editor IA:** "Crea `loyverse_integration/urls.py` con rutas para `connect_loyverse` y `loyverse_callback`. Muéstrame cómo incluir estas rutas en el `urls.py` principal del proyecto bajo el namespace `loyverse`."

**Tarea 2.2: Implementar Vista `connect_loyverse_view`**
*   **Acción:** En `loyverse_integration/views.py`:
    *   Debe ser una vista que requiera autenticación (`@login_required`).
    *   Obtener `LOYVERSE_APP_CLIENT_ID` de las variables de entorno.
    *   Definir el `REDIRECT_URI` (debe coincidir con lo configurado en Loyverse Developer Dashboard y ser una URL absoluta de tu vista de callback).
    *   Definir los `SCOPES` requeridos (ej. `"OPENID ITEMS_READ ITEMS_WRITE"`).
    *   Generar un `state` (string aleatorio, ej. usando `secrets.token_urlsafe()`) y guardarlo en `request.session['loyverse_oauth_state']`.
    *   Construir la URL de autorización de Loyverse: `https://api.loyverse.com/oauth/authorize?client_id={...}&scope={...}&response_type=code&redirect_uri={...}&state={...}`.
    *   Retornar `HttpResponseRedirect` a esa URL.
*   **Instrucción al Editor IA:** "Implementa la vista `connect_loyverse_view` en `loyverse_integration/views.py`. La vista debe ser protegida con `@login_required`. Debe obtener `LOYVERSE_APP_CLIENT_ID` de `os.environ`. Define un `REDIRECT_URI` (ej. `reverse('loyverse:loyverse_callback')` construido de forma absoluta). Define los `SCOPES`. Genera y almacena el `state` en la sesión. Construye la URL de autorización de Loyverse y redirige al usuario."

**Tarea 2.3: Implementar Vista `loyverse_callback_view`**
*   **Acción:** En `loyverse_integration/views.py`:
    1.  Obtener `code` y `state` de `request.GET`.
    2.  Verificar `state` contra el guardado en `request.session.pop('loyverse_oauth_state', None)`. Si no coincide o no existe, mostrar error.
    3.  Obtener `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET` de variables de entorno.
    4.  Hacer una petición POST a `https://api.loyverse.com/oauth/token` con `requests`:
        *   `data = {'client_id': LOYVERSE_APP_CLIENT_ID, 'client_secret': LOYVERSE_APP_CLIENT_SECRET, 'redirect_uri': REDIRECT_URI, 'code': code, 'grant_type': 'authorization_code'}`
        *   `headers = {'Content-Type': 'application/x-www-form-urlencoded'}`
    5.  Manejar la respuesta:
        *   Si es exitosa (status 200):
            *   Parsear el JSON: `access_token`, `refresh_token`, `expires_in`, `scope`, `id_token`.
            *   Calcular `expires_at = timezone.now() + timedelta(seconds=data['expires_in'])`.
            *   **Decodificar `id_token`:**
                *   Instalar `PyJWT` y `cryptography` (si `PyJWT` lo necesita para algoritmos RS256 y no está ya por `django-fernet-fields`).
                *   Obtener las claves públicas de `https://api.loyverse.com/.well-known/jwks.json`.
                *   Usar `jwt.decode(id_token, key=public_key, algorithms=['RS256'], audience=LOYVERSE_APP_CLIENT_ID, issuer='https://api.loyverse.com')` para verificar y decodificar. (La obtención y caché de la `public_key` correcta del JWKS es importante).
                *   Extraer `sub`, `name`, `email` del payload del `id_token`.
            *   Crear o actualizar el objeto `LoyverseUserConnection` para `request.user`:
                *   `loyverse_user_subject = id_token_payload['sub']`
                *   `access_token = access_token` (se cifrará por el modelo)
                *   `refresh_token = refresh_token` (se cifrará por el modelo)
                *   `expires_at = expires_at`
                *   `scope = scope_from_response`
                *   `loyverse_account_name = id_token_payload.get('name')`
                *   `loyverse_email = id_token_payload.get('email')`
                *   `is_active = True`
                *   `last_error_message = None`
            *   Guardar el objeto.
            *   Redirigir al usuario a una página de éxito (ej. su dashboard).
        *   Si falla: Mostrar un mensaje de error al usuario. Registrar el error.
*   **Instrucción al Editor IA:** "Implementa la vista `loyverse_callback_view`. Incluye verificación del `state`, la petición POST para intercambiar el código por tokens, el parseo de la respuesta. Para la decodificación del `id_token` con `PyJWT` y JWKS, proporcióna el esqueleto de la lógica o indica los pasos clave y las librerías necesarias."

**[COMPLETADA] Tarea 2.4: Implementar Lógica de Refresco de Token en `LoyverseUserConnection`**
*   **Estado:** Completada
*   **Acción:** 
    1. Se mejoró el método `refresh_access_token()` en el modelo `LoyverseUserConnection`:
       * Se implementó la obtención de credenciales desde variables de entorno.
       * Se añadió timeout de 10 segundos para evitar bloqueos en la petición.
       * Se mejoró el manejo de errores, incluyendo errores de timeout y ampliando el reconocimiento de errores para incluir `invalid_token` además de `invalid_grant`.
    2. Se mejoró el método `get_valid_access_token()` para usar `is_access_token_expired()` y llamar a `refresh_access_token()` cuando sea necesario.
    3. Se implementó un nuevo método `test_token_validity()` que verifica si el token sigue siendo válido haciendo una petición a la API de Loyverse.
    4. Se mejoró el método `record_sync_attempt()` para usar correctamente las constantes de clase `SyncStatus`.
*   **Nota:** Los tokens se manejan correctamente con el cifrado/descifrado automático proporcionado por `django-cryptography`. La lógica de refresco ahora es más robusta y maneja mejor los diferentes escenarios de error.

---

## Fase 3: Tarea Celery para Sincronización de Precios

**Objetivo:** Crear una tarea Celery que pueda ser invocada para sincronizar los precios de un usuario con su cuenta Loyverse.

**Tarea 3.1: Crear Tarea Celery `sync_loyverse_prices_for_user`**
*   **Acción:** En `loyverse_integration/tasks.py`:
    *   Definir una tarea `@shared_task(bind=True, max_retries=3, default_retry_delay=5*60)` llamada `sync_loyverse_prices_for_user`.
    *   La tarea recibirá `loyverse_connection_id` (el ID del objeto `LoyverseUserConnection`).
    *   Obtener la instancia de `LoyverseUserConnection`.
    *   Actualizar `price_sync_status` a `'SYNCING'` y `last_price_sync_start_time`.
    *   Llamar a `loyverse_connection.get_valid_access_token()` para obtener el `access_token`.
        *   Si falla (token inválido y no se pudo refrescar), actualizar `price_sync_status` a `'TOKEN_INVALID'`, marcar `loyverse_connection.is_active = False`, guardar y finalizar/notificar.
    *   **Reutilizar/Adaptar Lógica del Script Existente:**
        *   `get_local_products()`: Adaptar para obtener productos asociados al `loyverse_connection.user`.
        *   `get_all_loyverse_items()`: Usará el `access_token` obtenido.
        *   Bucle principal de comparación y actualización:
            *   **Implementar `time.sleep(1.05)` antes de cada `requests.post` a Loyverse para actualizar precios.**
            *   **Implementar manejo de error HTTP 429 con reintentos y backoff exponencial para las llamadas `POST` individuales.**
            *   Registrar éxitos y fallos individuales.
    *   Al finalizar:
        *   Actualizar `price_sync_status` a `'COMPLETED'`, `'COMPLETED_WITH_ERRORS'`, o `'FAILED'`.
        *   Guardar `last_price_sync_end_time`.
        *   Guardar un resumen en `last_price_sync_details` (JSONField, ej. `{'total_loyverse': X, 'total_local': Y, 'updated': Z, 'skipped': W, 'errors': [{'product_name': P, 'error': E}, ...]}`).
*   **Instrucción al Editor IA:** "Crea la tarea Celery `sync_loyverse_prices_for_user` en `loyverse_integration/tasks.py`. La tarea debe:
    1.  Aceptar `loyverse_connection_id`.
    2.  Obtener el objeto `LoyverseUserConnection` y actualizar su estado a `SYNCING`.
    3.  Obtener un `access_token` válido usando `get_valid_access_token()`. Manejar fallo de obtención de token.
    4.  Adaptar la lógica principal de mi script de actualización de precios (que te proporcioné anteriormente) para que funcione dentro de esta tarea, usando el `access_token` y obteniendo productos locales filtrados por el usuario de la conexión.
    5.  **Crucial: Antes de cada llamada `requests.post` para actualizar un precio en Loyverse, insertar `time.sleep(1.05)`.**
    6.  Implementar un bucle de reintentos con backoff para las llamadas `POST` si se recibe un HTTP 429.
    7.  Al finalizar, actualizar los campos de estado y detalles de la sincronización en el objeto `LoyverseUserConnection`."

---

## Fase 4: Interfaz de Usuario y Disparadores

**Objetivo:** Permitir a los usuarios iniciar la conexión y la sincronización.

**Tarea 4.1: Vista/Botón para Iniciar Sincronización de Precios**
*   **Acción:** En una vista de Django (accesible por el usuario autenticado, quizás en su dashboard):
    *   Obtener la `LoyverseUserConnection` del usuario.
    *   Si existe y está activa, y no está ya `SYNCING` o `QUEUED`, encolar la tarea Celery: `sync_loyverse_prices_for_user.delay(loyverse_connection.id)`.
    *   Actualizar `loyverse_connection.price_sync_status` a `'QUEUED'`.
    *   Mostrar un mensaje al usuario (ej. "Sincronización de precios iniciada...").
*   **Instrucción al Editor IA:** "Crea una vista simple en Django (ej. `trigger_price_sync_view`) que permita a un usuario logueado iniciar la tarea `sync_loyverse_prices_for_user` para su conexión Loyverse. Actualiza el estado de la conexión a `QUEUED`."

**Tarea 4.2: Mostrar Estado de Conexión y Sincronización al Usuario**
*   **Acción:** En las plantillas de Django (o componentes de React si el frontend ya está separado):
    *   Mostrar si el usuario tiene una conexión Loyverse activa.
    *   Mostrar el `price_sync_status`, `last_price_sync_end_time`, y un resumen de `last_price_sync_details`.
    *   Proporcionar el botón "Conectar con Loyverse" (que apunta a `loyverse:connect_loyverse`) si no está conectado.
    *   Proporcionar el botón "Sincronizar Precios Ahora" si está conectado y no en progreso.
*   **Instrucción al Editor IA:** "Describe cómo podría mostrar el estado de la conexión Loyverse y el estado de la sincronización de precios en una plantilla de Django, obteniendo los datos del objeto `LoyverseUserConnection` asociado al usuario actual."

---

## Fase 5: Pruebas, Refinamiento y Despliegue

**Objetivo:** Asegurar la calidad y preparar para producción.

*   **Pruebas Manuales Exhaustivas:** Probar todo el flujo OAuth2, la sincronización de precios para diferentes escenarios (pocos productos, muchos productos, errores de API).
*   **Revisión de Logs:** Celery, Django, Gunicorn.
*   **Optimización de Consultas:** Si la obtención de productos locales o la actualización de estados se vuelve lenta.
*   **Manejo de Errores:** Asegurar que todos los errores sean capturados y manejados graciosamente.
*   **Guía de Migración a Producción:** Seguir los pasos definidos en `CONTEXTO_PROYECTO.md`.

---