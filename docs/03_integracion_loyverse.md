# Integración con Loyverse

## 1. Introducción

La integración con Loyverse es un componente central de BodegaClick, permitiendo la sincronización bidireccional entre el sistema de gestión de inventario y la plataforma de punto de venta (POS). Esta documentación detalla cómo funciona esta integración, sus componentes principales y cómo configurarla correctamente.

Loyverse es una solución POS que permite gestionar ventas, inventario y clientes desde dispositivos móviles y web. BodegaClick se integra con Loyverse para mantener sincronizados los productos, precios e inventario, permitiendo una gestión centralizada mientras se aprovechan las capacidades del POS.

## 2. Arquitectura de la Integración

### 2.1 Componentes Principales

La integración con Loyverse se implementa a través de varios módulos en el directorio `backend/loyverse_sync/`:

1. **API (`api.py`)**: Gestiona la comunicación directa con la API de Loyverse, incluyendo autenticación, manejo de errores y caché.
2. **Productos (`products.py`)**: Implementa la lógica de importación y exportación de productos entre BodegaClick y Loyverse.
3. **Sincronización (`sync.py`)**: Coordina el proceso completo de sincronización, orquestando las operaciones de importación y exportación.
4. **Webhooks (`webhook/`)**: Maneja las notificaciones en tiempo real desde Loyverse cuando ocurren cambios en su sistema.

### 2.2 Flujo de Datos

```
┌─────────────────┐      ┌───────────────┐      ┌─────────────┐
│                 │      │               │      │             │
│  BodegaClick    │◄────►│  API Loyverse │◄────►│   Loyverse  │
│  (Django)       │      │   (REST)      │      │   (POS)     │
│                 │      │               │      │             │
└────────┬────────┘      └───────────────┘      └─────────────┘
         │                       ▲
         │                       │
         ▼                       │
┌─────────────────┐      ┌───────────────┐
│                 │      │               │
│  Base de Datos  │      │   Webhooks    │
│  (PostgreSQL)   │      │   (Eventos)   │
│                 │      │               │
└─────────────────┘      └───────────────┘
```

## 3. Configuración de la API de Loyverse

### 3.1 Obtención del Token de API

Para integrar BodegaClick con Loyverse, necesitas un token de API:

1. Inicia sesión en el [Panel de Administración de Loyverse](https://admin.loyverse.com/)
2. Ve a **Configuración** > **Integraciones** > **API**
3. Crea un nuevo token de API con los permisos necesarios:
   - `items:read` - Para leer información de productos
   - `items:write` - Para actualizar productos
   - `inventory:read` - Para leer niveles de inventario
   - `inventory:write` - Para actualizar inventario
   - `webhooks:read` - Para leer configuración de webhooks
   - `webhooks:write` - Para configurar webhooks

### 3.2 Configuración en BodegaClick

El token de API debe configurarse como variable de entorno:

```env
LOYVERSE_API_TOKEN=tu_token_de_loyverse
```

## 4. Sincronización de Productos

### 4.1 Importación desde Loyverse

La importación de productos desde Loyverse a BodegaClick se realiza mediante la función `importar_productos()` en `products.py`. Este proceso:

1. Obtiene todos los productos desde Loyverse usando la API
2. Filtra los productos según criterios especificados (categorías, IDs, etc.)
3. Para cada producto:
   - Si no existe en BodegaClick, lo crea
   - Si existe, actualiza sus datos manteniendo el precio base en USD intacto
   - Gestiona productos eliminados en Loyverse

**Características clave:**
- Preserva los precios base en USD configurados en BodegaClick
- Permite filtrado por categorías específicas
- Maneja productos con variantes
- Registra estadísticas detalladas del proceso

### 4.2 Exportación hacia Loyverse

La exportación de precios desde BodegaClick hacia Loyverse se realiza mediante la función `exportar_precios()` en `products.py`. Este proceso:

1. Obtiene productos de BodegaClick según criterios de filtrado
2. Calcula los precios actualizados basados en tasas de cambio
3. Aplica reglas de redondeo especiales para precios en bolívares
4. Actualiza los precios en Loyverse mediante la API
5. Procesa los productos en lotes para evitar sobrecargar la API

**Características clave:**
- Actualización selectiva por tipo de tasa (BCV o PARALELO)
- Procesamiento por lotes configurable
- Verificación de diferencias de precio antes de actualizar
- Manejo de errores con reintentos automáticos

### 4.3 Redondeo Especial de Precios

BodegaClick implementa una lógica especial de redondeo para precios en bolívares mediante la función `aplicar_redondeo_especial()`. Esta lógica:

1. Aplica diferentes reglas según el rango de precios
2. Redondea a valores específicos para facilitar el manejo de efectivo
3. Mantiene consistencia entre frontend y backend

## 5. Webhooks de Loyverse

### 5.1 Configuración de Webhooks

Los webhooks permiten a Loyverse notificar a BodegaClick cuando ocurren cambios en su sistema. Para configurarlos:

1. Usa el script `create_webhook.py` para registrar endpoints en Loyverse:
   ```bash
   python create_webhook.py --type inventory_levels.update --url https://tu-dominio.com/api/webhooks/inventory
   ```

2. Tipos de webhooks soportados:
   - `inventory_levels.update`: Notifica cambios en niveles de inventario
   - `items.update`: Notifica cambios en productos
   - `customers.update`: Notifica cambios en clientes
   - `receipts.update`: Notifica nuevas ventas o cambios en recibos
   - `shifts.create`: Notifica apertura/cierre de turnos

### 5.2 Procesamiento de Eventos

Cuando Loyverse envía una notificación vía webhook:

1. BodegaClick verifica la firma del webhook para autenticar su origen
2. Procesa el evento según su tipo
3. Actualiza la base de datos local según corresponda
4. Registra la actividad en logs para auditoría

### 5.3 Prueba de Webhooks

Para probar la recepción de webhooks sin necesidad de eventos reales en Loyverse:

```bash
python webhook/test_webhook.py --url http://localhost:8000/api/webhooks/inventory --type inventory_levels.update --secret tu_secreto
```

Este script simula eventos de Loyverse, permitiendo verificar que tu aplicación los procesa correctamente.

## 6. Optimizaciones y Buenas Prácticas

### 6.1 Caché de Respuestas

La integración implementa un sistema de caché para reducir llamadas a la API de Loyverse:

- Las respuestas se almacenan en memoria durante un período configurable (15 minutos por defecto)
- Se puede limpiar el caché manualmente con `clear_cache()` cuando se necesiten datos frescos
- Reduce la latencia y evita alcanzar límites de tasa de la API

### 6.2 Manejo de Errores y Reintentos

La integración incluye un sistema robusto de manejo de errores:

- Reintentos automáticos con backoff exponencial para errores temporales
- Logging detallado con niveles de severidad apropiados
- Transacciones de base de datos para mantener consistencia

### 6.3 Sincronización Selectiva

Para mejorar el rendimiento, la sincronización puede ser selectiva:

- Por categorías específicas de productos
- Por tipo de tasa de cambio (BCV o PARALELO)
- Por IDs específicos de productos
- Procesamiento por lotes de tamaño configurable

## 7. Comandos y Scripts Útiles

### 7.1 Sincronización Completa

```bash
python manage.py shell -c "from loyverse_sync.sync import sincronizar_desde_loyverse; sincronizar_desde_loyverse()"
```

### 7.2 Importar Productos sin Exportar Precios

```bash
python manage.py shell -c "from loyverse_sync.sync import sincronizar_desde_loyverse; sincronizar_desde_loyverse({'solo_importar': True})"
```

### 7.3 Sincronizar Categoría Específica

```bash
python manage.py shell -c "from loyverse_sync.sync import sincronizar_desde_loyverse; sincronizar_desde_loyverse({'categorias': ['Bebidas']})"
```

### 7.4 Sincronizar por Tipo de Tasa

```bash
python manage.py shell -c "from loyverse_sync.sync import sincronizar_desde_loyverse; sincronizar_desde_loyverse({'tipo_tasa': 'BCV'})"
```

## 8. Solución de Problemas

### 8.1 Errores Comunes

| Error | Posible Causa | Solución |
|-------|---------------|----------|
| 401 Unauthorized | Token de API inválido o expirado | Regenerar token en panel de Loyverse |
| 429 Too Many Requests | Límite de tasa excedido | Aumentar tamaño de lote o implementar delays |
| Precios inconsistentes | Redondeo incorrecto | Verificar función `aplicar_redondeo_especial()` |
| Productos duplicados | IDs de Loyverse inconsistentes | Limpiar productos y reimportar |

### 8.2 Verificación de Sincronización

Para verificar que la sincronización funciona correctamente:

1. Revisa los logs en `loyverse_sync.log`
2. Compara precios entre BodegaClick y Loyverse para productos específicos
3. Verifica que los webhooks estén recibiendo eventos (revisa logs de servidor)

### 8.3 Diagnóstico

Si encuentras problemas con la sincronización:

1. Habilita logging detallado en `settings.py`
2. Usa el modo de prueba para sincronizar productos específicos:
   ```python
   sincronizar_desde_loyverse({'productos_ids': ['id1', 'id2']})
   ```
3. Verifica la conectividad con la API de Loyverse:
   ```bash
   curl -H "Authorization: Bearer TU_TOKEN" https://api.loyverse.com/v1.0/items
   ```

## 9. Consideraciones de Seguridad

- El token de API debe mantenerse seguro y no debe incluirse en el código fuente
- Configura correctamente CORS para los endpoints de webhook
- Verifica siempre la firma de los webhooks entrantes
- Implementa rate limiting en tus endpoints de webhook para prevenir ataques DoS
- Rota periódicamente el token de API de Loyverse

## 10. Próximas Mejoras

- Implementación de cola de tareas con Celery para sincronización asíncrona
- Sincronización de clientes y ventas
- Panel de control para monitorear estado de sincronización
- Alertas automáticas para fallos de sincronización
- Expansión de webhooks para más tipos de eventos

---

*Última actualización: 26 de junio de 2025*
