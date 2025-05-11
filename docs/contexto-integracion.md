# Contexto del Proyecto para el Módulo de Integración con Loyverse en BodegaClick

## 1. Stack Tecnológico Principal de BodegaClick:
*   **Backend:** Django 4.2.0, Django REST Framework 3.14.0
*   **Procesamiento Asíncrono:** Celery 5.4.0 con Redis 5.2.1 como broker/backend.
*   **Servidor Web Backend:** Gunicorn 21.2.0
*   **Base de Datos:** PostgreSQL 13 (Compatible con Neon, Railway, Coolify).
*   **Frontend:** React (Node.js 16) servido por Nginx.
*   **Contenerización:** Docker y Docker Compose para todos los servicios.
*   **Gestión de Variables de Entorno:** `.env` y `python-dotenv`. Credenciales sensibles siempre por variables de entorno.
*   **Despliegue:** Coolify (previamente Railway), usando Dockerfiles.

## 2. Objetivo General del Módulo:
Permitir que los usuarios de BodegaClick (que son negocios/tiendas) conecten sus **propias cuentas individuales de Loyverse** de forma segura para sincronizar datos. La funcionalidad inicial se centrará en la **actualización de precios de productos** desde BodegaClick hacia Loyverse.

## 3. Autenticación con Loyverse:
*   Se utilizará **OAuth 2.0** según la documentación de Loyverse.
*   BodegaClick (como aplicación) necesitará un `client_id` y `client_secret` globales (registrados en el Developer Dashboard de Loyverse) para iniciar el flujo OAuth2 para cada usuario. Estos se gestionarán como variables de entorno seguras para la aplicación BodegaClick.
*   **Flujo por Usuario:**
    1.  El usuario de BodegaClick será redirigido a Loyverse para autorizar a BodegaClick el acceso a SU cuenta Loyverse.
    2.  Loyverse devolverá un `authorization_code`.
    3.  BodegaClick intercambiará este `code` (junto con su `client_id` y `client_secret` globales) por un `access_token` y un `refresh_token` **específicos para ese usuario y su cuenta Loyverse**.
*   Los `access_token` expiran (ej. 12 horas, según la documentación de Loyverse) y BodegaClick debe ser capaz de refrescarlos usando el `refresh_token` del usuario.
*   **Scopes Requeridos Inicialmente (pueden expandirse):** `ITEMS_READ`, `ITEMS_WRITE`, `OPENID`. Se solicitará el scope `OPENID` para obtener información identificativa del usuario/cuenta en Loyverse.
*   Se extraerá información del `id_token` (JWT) como `sub` (identificador único del usuario/cuenta en Loyverse), `name` (nombre del negocio en Loyverse), `email` (email de la cuenta Loyverse).

## 4. Estructura del Proyecto Django Actual:
*   El proyecto Django (`config.settings`) ya existe.
*   Existe una app principal `facturacion` con modelos como `Producto`, `Factura`, etc. (ver schema de BD proporcionado).
*   Se utiliza el sistema de autenticación de usuarios de Django (`django.contrib.auth.models.User`).
*   `django-celery-results` ya está integrado.
*   Se creará una **nueva app de Django** llamada `loyverse_integration` para toda la lógica de esta nueva integración.

## 5. Requisitos de Almacenamiento de Datos (para la nueva app `loyverse_integration`):
*   **Modelo `LoyverseAppCredential` (Singleton o Configuración Global):**
    *   Almacenará el `client_id` y `client_secret` de la aplicación BodegaClick.
    *   El `client_secret` **DEBE** estar cifrado en la base de datos (usando `django-fernet-fields`).
    *   Esta información se cargará preferentemente desde variables de entorno al iniciar la aplicación, pero tener un modelo puede facilitar la gestión en algunos escenarios o si se necesita rotar credenciales vía interfaz administrativa (con extrema precaución). Alternativamente, acceder directamente a las variables de entorno desde el código puede ser más simple si estas credenciales no cambian frecuentemente. **Priorizar el uso directo de variables de entorno para `client_id` y `client_secret` de la app.** Si se usa un modelo, debe ser para una única configuración global.
*   **Modelo `LoyverseUserConnection` (Uno por Usuario de BodegaClick conectado a Loyverse):**
    *   Relación `OneToOneField` con `settings.AUTH_USER_MODEL`.
    *   `access_token` (cifrado con `django-fernet-fields`).
    *   `refresh_token` (cifrado con `django-fernet-fields`).
    *   `token_type` (ej. "Bearer").
    *   `expires_at` (DateTimeField para la expiración del `access_token`).
    *   `scope` (TextField, scopes concedidos por el usuario).
    *   `loyverse_user_subject` (CharField, `sub` de OpenID, debe ser `unique=True` si se espera que una cuenta Loyverse solo pueda ser conectada por un usuario de BodegaClick).
    *   `loyverse_merchant_id` (CharField, opcional, si es útil).
    *   `loyverse_account_name` (CharField, `name` de OpenID).
    *   `loyverse_email` (EmailField, `email` de OpenID).
    *   `is_active` (BooleanField, indica si la conexión es utilizable).
    *   `last_token_refresh_time` (DateTimeField).
    *   `last_error_message` (TextField).
    *   Campos para el estado de sincronización de precios: `price_sync_status` (CharField con choices), `last_price_sync_start_time`, `last_price_sync_end_time`, `last_price_sync_details` (JSONField para resumen/errores).

## 6. Funcionalidades Clave del Módulo `loyverse_integration`:
1.  **Flujo OAuth2 Completo:** Implementar las vistas y lógica para el inicio de la conexión, manejo del callback, intercambio de código por tokens, almacenamiento seguro de tokens, y refresco automático de `access_token`.
2.  **Tarea Celery para Sincronización de Precios:**
    *   Una tarea por `LoyverseUserConnection` para actualizar los precios de todos los productos vinculados.
    *   Obtendrá el `access_token` válido del usuario (refrescándolo si es necesario).
    *   **Respetará el límite de tasa de la API de Loyverse: 1 petición POST / segundo / token de cuenta (por `LoyverseUserConnection`). Esto se implementará con `time.sleep(1.05)` antes de cada llamada `POST` dentro de la tarea.**
    *   Manejará errores HTTP 429 (Too Many Requests) de la API con reintentos y backoff exponencial.
    *   Actualizará los estados de sincronización en el modelo `LoyverseUserConnection`.
3.  **Interfaz de Usuario (Inicialmente en el Admin de Django, luego potencialmente en el frontend de React):**
    *   Administrador: Ver y gestionar `LoyverseAppCredential` (si se opta por el modelo, sino se configura por ENV VARS). Ver conexiones de usuarios (`LoyverseUserConnection`).
    *   Usuario Final (en su panel de BodegaClick):
        *   Botón "Conectar con Loyverse" para iniciar el flujo OAuth2.
        *   Visualización del estado de su conexión (Conectado/Desconectado, último error).
        *   Botón "Sincronizar Precios Ahora" (que encolará la tarea Celery).
        *   Visualización del estado de la última sincronización de precios.
        *   Opción para "Desconectar de Loyverse" (que debería invalidar/eliminar los tokens almacenados).

## 7. Consideraciones de Seguridad:
*   `client_secret` de la app BodegaClick y los `access_token`/`refresh_token` de los usuarios DEBEN estar cifrados en la base de datos. Se usará `django-fernet-fields`.
*   Las claves de cifrado (Fernet keys) deben gestionarse como secretos (variables de entorno).
*   Proteger las vistas de callback OAuth2 contra CSRF (usando el parámetro `state`).

## 8. Migración de Estructuras entre Entornos (Desarrollo/Prueba a Producción):
*   El desarrollo del módulo se hará en un entorno de prueba.
*   Para pasar a producción:
    1.  **BACKUP COMPLETO de la BD de producción.**
    2.  Desplegar el nuevo código (con la app `loyverse_integration` y sus migraciones).
    3.  Ejecutar `python manage.py migrate` en producción para crear las nuevas tablas (`loyverseintegration_loyverseappcredential`, `loyverseintegration_loyverseuserconnection`).
    4.  Configurar las variables de entorno en producción para `DJANGO_FERNET_KEY` y las credenciales `LOYVERSE_CLIENT_ID`, `LOYVERSE_CLIENT_SECRET` de la aplicación BodegaClick.
    5.  Los usuarios existentes de BodegaClick necesitarán pasar por el flujo de conexión OAuth2 para vincular sus cuentas Loyverse. No habrá "migración de datos de tokens" desde prueba, ya que cada conexión es nueva y específica del usuario en producción.

## 9. Documentación de Loyverse API para Autenticación:
*   (Se adjunta la documentación proporcionada previamente sobre "Personal Access Tokens" y "OAuth 2.0"). Se priorizará OAuth 2.0.

## 10. Contexto de Integración: Módulo Loyverse para BodegaClick

Este documento describe la arquitectura, componentes clave y decisiones de diseño para el módulo de integración entre BodegaClick y Loyverse. El objetivo principal de este módulo es permitir a los usuarios de BodegaClick conectar sus cuentas de Loyverse de forma segura mediante OAuth 2.0 y sincronizar datos, comenzando con los precios de los productos.

Este contexto se desarrollará incrementalmente a medida que se completen las fases del plan de desarrollo.

---

## Fase 1: Configuración Inicial, Modelos de Datos y Cifrado

**Objetivo Principal de la Fase:** Establecer la infraestructura básica para la integración con Loyverse, incluyendo la nueva aplicación Django, la definición de modelos de datos para las conexiones de usuario y la implementación del cifrado para datos sensibles.

**Componentes y Decisiones Clave:**

1.  **Creación de la App Django `loyverse_integration`:**
    *   Se ha creado una nueva aplicación Django dedicada llamada `loyverse_integration` para encapsular toda la lógica relacionada con la integración de Loyverse.
    *   Esta aplicación ha sido registrada en `INSTALLED_APPS` en la configuración del proyecto (`config/settings.py`).

2.  **Cifrado de Datos Sensibles con `django-fernet-fields`:**
    *   Se ha integrado la librería `django-fernet-fields` para asegurar el cifrado de datos sensibles como tokens de acceso y tokens de refresco.
    *   La clave de cifrado (`DJANGO_FERNET_KEY`) se gestiona como una variable de entorno, almacenada en el archivo `.env` y en la configuración del entorno de despliegue, y se carga en `config/settings.py` a través de la variable `FERNET_KEYS`.

3.  **Gestión de Credenciales de la Aplicación Loyverse:**
    *   Las credenciales globales de la aplicación BodegaClick para interactuar con la API de Loyverse (`LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET`) se accederán directamente desde las variables de entorno.
    *   Se ha decidido no crear un modelo `LoyverseAppCredential` por ahora para simplificar la configuración inicial, ya que estas credenciales son estáticas y no requieren una interfaz de gestión.

4.  **Definición del Modelo `LoyverseUserConnection`:**
    *   Se ha definido el modelo `LoyverseUserConnection` en `loyverse_integration/models.py`.
    *   Este modelo almacena la información de conexión OAuth 2.0 específica de cada usuario de BodegaClick que se conecta a Loyverse.
    *   Campos clave incluyen:
        *   `user`: Una relación `OneToOneField` al modelo de usuario de Django (`settings.AUTH_USER_MODEL`).
        *   `access_token`: Token de acceso OAuth, cifrado usando `EncryptedTextField`.
        *   `refresh_token`: Token de refresco OAuth, cifrado usando `EncryptedTextField`.
        *   `expires_at`: Fecha y hora de expiración del `access_token`.
        *   `scope`: Los permisos otorgados.
        *   `loyverse_user_subject`: El identificador único del usuario en Loyverse (del `id_token`).
        *   `loyverse_account_name`: Nombre de la cuenta/tienda en Loyverse.
        *   `loyverse_email`: Email asociado a la cuenta Loyverse.
        *   `is_active`: Booleano que indica si la conexión está activa.
        *   `price_sync_status`: Estado de la sincronización de precios (ej. `IDLE`, `SYNCING`, `COMPLETED`).
        *   `last_price_sync_start_time`, `last_price_sync_end_time`, `last_price_sync_details` (`JSONField`).
        *   `created_at`, `updated_at`.

5.  **Migraciones de Base de Datos:**
    *   Se han creado y aplicado las migraciones iniciales para la aplicación `loyverse_integration` para reflejar el nuevo modelo `LoyverseUserConnection` en la base de datos.
    *   Comandos ejecutados: `python manage.py makemigrations loyverse_integration` y `python manage.py migrate loyverse_integration`.

6.  **Registro en el Admin de Django:**
    *   El modelo `LoyverseUserConnection` se ha registrado en el panel de administración de Django (`loyverse_integration/admin.py`).
    *   Se ha configurado `list_display` para mostrar campos relevantes como `user`, `loyverse_account_name`, `is_active`, `price_sync_status`, y `updated_at` para facilitar la supervisión.

---