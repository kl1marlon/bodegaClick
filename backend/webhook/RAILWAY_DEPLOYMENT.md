# Despliegue de Webhooks en Railway

Este documento describe los pasos para desplegar y configurar correctamente los webhooks de Loyverse en un entorno de producción usando Railway.

## Ventajas de Railway para webhooks

Railway es ideal para desplegar webhooks porque:

1. **Proporciona URLs HTTPS automáticamente**: Loyverse requiere HTTPS para los webhooks
2. **Alta disponibilidad**: Minimiza el riesgo de perder notificaciones
3. **Logs integrados**: Facilita el diagnóstico de problemas
4. **Escalabilidad automática**: Maneja picos de tráfico sin configuración adicional

## Prerrequisitos

1. **Cuenta en Railway**: Regístrate en [railway.app](https://railway.app)
2. **Proyecto configurado**: Ya debes tener tu proyecto BodegaClick desplegado en Railway
3. **Acceso a la API de Loyverse**: Token de API válido
4. **Configuración OAuth 2.0**: Configurado para recibir el encabezado de firma

## Configuración de OAuth 2.0 para Webhooks

Según la documentación oficial y la experiencia real de desarrolladores, para recibir el encabezado `X-Loyverse-Signature` necesario para la validación, debes:

1. **Configurar OAuth 2.0 en Loyverse**:
   - Sigue el proceso de [Autorización OAuth 2.0](https://developer.loyverse.com/docs/#section/Authorization/OAuth-2.0)
   - Obtén un token de acceso válido
   - Utiliza este token para crear los webhooks a través de la API

2. **Crear los webhooks con el token OAuth**:
   - Puedes usar Postman u otra herramienta para realizar la solicitud inicial
   - El endpoint para crear webhooks es `POST https://api.loyverse.com/v1.0/webhooks`
   - Incluye el token OAuth en el encabezado de autorización

Sin esta configuración OAuth 2.0, los webhooks no incluirán el encabezado de firma necesario para la validación segura.

## Proceso de despliegue

### 1. Preparar las variables de entorno

En Railway, agrega o actualiza las siguientes variables de entorno:

- `LOYVERSE_API_TOKEN`: Tu token de API de Loyverse
- `LOYVERSE_WEBHOOK_SECRET`: Un secreto seguro para verificar webhooks

Si ya tienes tu aplicación desplegada, simplemente actualiza estas variables.

### 2. Verificar la configuración de URLs

Asegúrate de que tu aplicación tenga configurada correctamente la URL `/webhook/` en el archivo `urls.py`:

```python
urlpatterns = [
    # ... otras URLs ...
    path('webhook/', WebhookReceiveView.as_view(), name='webhook-receive'),
]
```

### 3. Crear los webhooks en Loyverse

Una vez desplegada la aplicación, debes crear los webhooks en Loyverse apuntando a tu dominio de Railway:

1. **Obtén la URL de tu aplicación** desde el panel de Railway (Ejemplo: `https://tu-app.up.railway.app`)

2. **Configura OAuth 2.0 y obtén un token de acceso**:
   - Sigue la documentación oficial para configurar OAuth 2.0
   - Guarda el token de acceso obtenido

3. **Ejecuta los scripts de creación de webhooks**:
   
   Puedes hacerlo de dos formas:

   **Opción 1**: Ejecuta los scripts localmente con la URL de producción
   ```bash
   # Crear webhook para inventario
   python backend/webhook/create_inventory_webhook.py --url https://tu-app.up.railway.app/webhook/
   
   # Crear webhook para productos
   python backend/webhook/create_items_webhook.py --url https://tu-app.up.railway.app/webhook/
   ```

   **Opción 2**: Usa Railway CLI para ejecutar los scripts en el entorno de producción
   ```bash
   # Instala Railway CLI si no lo tienes
   npm i -g @railway/cli
   
   # Inicia sesión
   railway login
   
   # Vincula al proyecto
   railway link

   # Ejecuta los scripts en Railway
   railway run python backend/webhook/create_inventory_webhook.py --url https://tu-app.up.railway.app/webhook/
   railway run python backend/webhook/create_items_webhook.py --url https://tu-app.up.railway.app/webhook/
   ```

### 4. Verificar la creación de webhooks

Verifica que los webhooks se hayan creado correctamente:

1. **Consulta el panel de Loyverse** para ver los webhooks registrados
2. **Revisa los logs de Railway** para confirmar que no hay errores
3. **Verifica que recibes el encabezado `X-Loyverse-Signature`** en las peticiones
4. **Haz una prueba práctica** modificando un producto o inventario en Loyverse

### 5. Configurar monitoreo

Para asegurar que los webhooks funcionen continuamente:

1. **Configura alertas en Railway** para notificar errores del servidor
2. **Implementa una tarea programada** que verifique periódicamente el estado de los webhooks

## Consideraciones de seguridad y validación

El sistema utiliza HMAC-SHA1 (no SHA-256 como indica parte de la documentación) para validar las firmas:

```python
# Validación correcta con HMAC-SHA1
expected = hmac.new(
    settings.LOYVERSE_WEBHOOK_SECRET.encode('utf-8'),
    payload,
    hashlib.sha1
).hexdigest()

# Comparar firmas
hmac.compare_digest(expected, signature)
```

## Resolución de problemas en producción

Si los webhooks no funcionan correctamente en Railway:

### 1. Verificar logs

```bash
railway logs
```

Busca errores relacionados con los webhooks:
- Problemas de firma inválida
- Errores de procesamiento de datos
- Excepciones no controladas

### 2. Verificar la recepción del encabezado de firma

Asegúrate de que estás recibiendo el encabezado `X-Loyverse-Signature` en las solicitudes:

```python
# Añade este código temporalmente para depuración
@api_view(['POST'])
def debug_headers(request):
    headers = dict(request.headers)
    body = request.body
    return Response({
        'headers': headers,
        'body_length': len(body)
    })
```

### 3. Regenerar los webhooks

Si es necesario, elimina y vuelve a crear los webhooks:

```bash
# Eliminar webhooks existentes
railway run python backend/webhook/cleanup_webhooks.py

# Crear nuevos webhooks
railway run python backend/webhook/create_inventory_webhook.py --url https://tu-app.up.railway.app/webhook/
railway run python backend/webhook/create_items_webhook.py --url https://tu-app.up.railway.app/webhook/
```

## Buenas prácticas para webhooks en producción

1. **Responde rápidamente**: Loyverse espera una respuesta HTTP 2xx en un tiempo razonable
2. **Procesa asincrónicamente**: Para operaciones largas, responde de inmediato y procesa en segundo plano
3. **Implementa reintentos**: Maneja fallos temporales con un sistema de reintentos
4. **Mantén logs detallados**: Registra todos los webhooks recibidos para diagnóstico
5. **Implementa verificación periódica**: Compara ocasionalmente los datos con Loyverse para detectar desincronizaciones

## Actualización y mantenimiento

1. **Actualiza periódicamente el secreto del webhook** por seguridad
2. **Mantente al día con cambios en la API de Loyverse**
3. **Realiza pruebas después de actualizar tu aplicación**

Con esta configuración, tendrás un sistema robusto de webhooks funcionando en un entorno de producción confiable. 