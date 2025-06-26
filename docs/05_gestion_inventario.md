# Sistema de Gestión de Inventario

## Descripción General
El sistema de gestión de inventario de BodegaClick permite monitorear y actualizar el stock de productos sincronizándose con la plataforma Loyverse. Proporciona mecanismos para consultar el inventario actual, generar alertas de stock bajo y sincronizar los niveles de stock entre ambos sistemas.

## Estructura de Datos

### Modelo `Producto` (Campos de Inventario)
- `stock_actual`: Almacena la cantidad disponible actualmente del producto.
- `ultima_actualizacion_stock`: Timestamp de la última vez que se actualizó la información de stock.
- `variant_id`: Identificador único de la variante de producto en Loyverse, necesario para operaciones de inventario.
- `loyverse_id`: Identificador único del producto en Loyverse.

## Flujo de Sincronización de Inventario

El proceso de sincronización de inventario sigue estos pasos:

1. **Obtención de Variant ID**: Si un producto no tiene `variant_id` pero sí tiene `loyverse_id`, se consulta la API de Loyverse para obtener el ID de variante correspondiente.

2. **Consulta de Niveles de Inventario**: Se hace una petición a la API de Loyverse para obtener los niveles actuales de inventario para una variante específica.

3. **Actualización de la Base de Datos Local**: Se actualiza el campo `stock_actual` y `ultima_actualizacion_stock` en la base de datos local.

## Scripts y Comandos

### `sync_inventory.py`
- Comando de Django para sincronizar el inventario con Loyverse.
- Soporta la opción `--force` para actualizar todos los productos, no solo los que tienen stock cero.
- Genera estadísticas de sincronización (productos actualizados, errores, etc.).

### Interfaz Web de Sincronización
- Permite ejecutar la sincronización de inventario desde una interfaz de usuario amigable.
- Ofrece opciones para sincronizar todos los productos o solo los que no tienen stock.
- Requiere un token de autenticación para mayor seguridad.

## Integración con Loyverse

### API de Inventario de Loyverse
- URL Base: `https://api.loyverse.com/v1.0`
- Endpoints utilizados:
  - `/items/{id}`: Para obtener detalles de productos y sus variantes.
  - `/inventory?variant_ids={id}`: Para consultar niveles de inventario específicos.

### Manejo de Rate Limiting
- Implementación de pausas entre peticiones para evitar alcanzar límites de la API:
  - Pausa de 1 segundo cada 5 productos procesados.
  - Pausa de 0.2 segundos cada 2 productos.

## Sistema de Notificación

### Componente `NotificacionInventario`
- Muestra alertas en la interfaz de usuario sobre productos con stock bajo o agotado.
- Permite marcar notificaciones como leídas o eliminarlas.
- Proporciona visualización clara y priorizada de las alertas de inventario.

## Seguridad y Autenticación

- Se requieren tokens de autenticación para operaciones de sincronización.
- La API de Loyverse utiliza tokens Bearer para autorización.
- Las operaciones sensibles están protegidas por validaciones de seguridad.

## Buenas Prácticas

1. **Sincronización Selectiva**: Priorizar la actualización de productos sin stock o de alta rotación.
2. **Monitoreo Regular**: Establecer intervalos regulares de sincronización para mantener datos actualizados.
3. **Manejo de Errores**: Implementar estrategias de retry para fallos temporales en la API.
4. **Auditoría**: Registrar cada operación de actualización de inventario para revisión posterior.

## Extensibilidad

- El sistema está diseñado para integrar con múltiples tiendas Loyverse (mediante `store_id`).
- La arquitectura permite incorporar otros sistemas de POS en el futuro.
- Los webhooks facilitan la actualización en tiempo real cuando hay cambios en Loyverse.

---

**Referencia de Archivos:**
- `backend/facturacion/models.py`: Modelo de datos para productos e inventario.
- `backend/facturacion/management/commands/sync_inventory.py`: Comando para sincronización.
- `backend/facturacion/templates/sincronizar_inventario.html`: Interfaz web de sincronización.
- `frontend/src/components/NotificacionInventario.jsx`: Componente de notificaciones.
