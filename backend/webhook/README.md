# Webhooks para Loyverse

Este directorio contiene herramientas para configurar y gestionar webhooks con Loyverse, permitiendo mantener sincronizados los datos entre BodegaClick y Loyverse en tiempo real.

## ¿Qué son los webhooks?

Los webhooks son notificaciones HTTP en tiempo real que Loyverse envía a tu aplicación cuando ocurren ciertos eventos, como:
- Cambios en el inventario
- Creación o modificación de productos
- Creación de órdenes
- Y más

## Webhooks implementados

Actualmente, BodegaClick implementa los siguientes webhooks:

1. **inventory_levels.update**: Actualiza el inventario en BodegaClick cuando cambia en Loyverse
2. **items.update**: Actualiza la información de productos cuando se crean, modifican o eliminan en Loyverse

## Herramientas disponibles

### Configuración y pruebas en desarrollo

- **test_webhook_local.py**: Configura webhooks para desarrollo local usando ngrok
  ```
  python backend/webhook/test_webhook_local.py
  ```

### Gestión de webhooks

- **create_items_webhook.py**: Crea un webhook para sincronización de productos
  ```
  python backend/webhook/create_items_webhook.py --url https://tu-dominio.com/webhook/
  ```

- **cleanup_webhooks.py**: Elimina webhooks configurados previamente
  ```
  python backend/webhook/cleanup_webhooks.py
  ```

- **update_webhook_secret.py**: Actualiza el secreto usado para verificar webhooks
  ```
  python backend/webhook/update_webhook_secret.py
  ```

## Desarrollo local

Para probar webhooks en desarrollo local:

1. **Instala ngrok** desde [ngrok.com](https://ngrok.com/download)

2. **Ejecuta el servidor Django**
   ```
   cd bodegaClick/backend
   python manage.py runserver
   ```

3. **Configura los webhooks con el asistente**
   ```
   python backend/webhook/test_webhook_local.py
   ```
   Este script te guiará en el proceso de:
   - Configurar ngrok
   - Crear los webhooks en Loyverse
   - Probar el funcionamiento

## Seguridad

### Autenticación y Verificación de Webhooks

Para recibir y validar correctamente los webhooks de Loyverse:

1. **Configuración con OAuth 2.0**:
   - Es necesario configurar los webhooks utilizando OAuth 2.0 para recibir el encabezado `X-Loyverse-Signature`.
   - Sigue el proceso de [Autorización OAuth 2.0](https://developer.loyverse.com/docs/#section/Authorization/OAuth-2.0) para obtener un token de acceso.
   - Usa este token para crear los webhooks a través de la API de Loyverse.
   - Sin esta configuración, no recibirás el encabezado de firma necesario para la validación.

2. **Validación de firmas**:
   - Cada webhook incluye un encabezado `X-Loyverse-Signature` generado usando el algoritmo **HMAC-SHA1**.
   - El servidor verifica esta firma usando el secreto del webhook y el cuerpo de la solicitud (payload).
   - Para validar, calculamos el HMAC del payload con nuestro secreto y lo comparamos con la firma.
   - Solo se procesan las solicitudes con firmas válidas.

### Actualización del Secreto

Para generar y actualizar el secreto usado en la verificación:
```
python backend/webhook/update_webhook_secret.py
```

## Configuración en producción

Para entornos de producción:

1. **Asegura que tu servidor tenga un dominio con HTTPS**
   - Railway proporcionará esto automáticamente

2. **Actualiza el secreto del webhook**
   ```
   python backend/webhook/update_webhook_secret.py
   ```

3. **Crea los webhooks apuntando a tu dominio de producción**
   ```
   python backend/webhook/create_items_webhook.py --url https://tu-app.up.railway.app/webhook/
   ```

4. **Verifica el funcionamiento** realizando cambios en Loyverse y confirmando que se reflejan en BodegaClick

## Resolución de problemas

Si los webhooks no funcionan correctamente:

1. **Verifica los logs del servidor** para mensajes de error
2. **Comprueba que el secreto sea correcto** en el archivo `.env`
3. **Asegúrate de que los webhooks estén habilitados** en el panel de Loyverse
4. **Elimina y vuelve a crear** los webhooks si es necesario
5. **Verifica que estés usando OAuth 2.0** para la creación de webhooks

Para eliminar todos los webhooks y empezar de nuevo:
```
python backend/webhook/cleanup_webhooks.py
``` 