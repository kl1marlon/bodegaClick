# Verificación de Precios Loyverse

## Cambios recientes en el flujo de actualización de precios

### Actualización masiva de precios base desde la interfaz
- Se implementó un endpoint en el backend (`/api/productos/actualizar-precios-base/`) que permite actualizar el campo `precio_base` de todos los productos, recibiendo la nueva tasa por POST.
- Este endpoint recorre todos los productos y recalcula su `precio_base` usando el campo `precio_base_usd` y la tasa enviada.
- Desde la interfaz (ListadoProductos.js) se agregará un botón para ejecutar esta acción de forma rápida y sencilla tras cambiar la tasa.
- El comando de management `actualizar_precios_base.py` sigue disponible para uso manual desde la terminal.

### Lógica de actualización individual
- Si el campo `precio_base_usd` de un producto cambia (por ejemplo, al registrar una nueva factura), el precio_base debe recalcularse usando la tasa vigente para mantener la integridad lógica.

### Decisión sobre workers
- Se descartó el uso de Celery/workers para mantener la solución simple y rápida. La actualización masiva se ejecuta como una petición HTTP y puede tomar algunos segundos dependiendo del número de productos.

---

Este documento se irá actualizando conforme se avance en la integración y pruebas del flujo de actualización de precios.
