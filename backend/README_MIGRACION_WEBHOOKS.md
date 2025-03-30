# Migración a Webhooks de Loyverse

Este documento describe los pasos necesarios para aplicar la migración que añade soporte completo para webhooks de Loyverse, especialmente para la sincronización de inventario en tiempo real.

## Pasos para la migración

### 1. Aplicar migración en Railway

Ejecuta el siguiente comando en la terminal de Railway para aplicar la migración que añade el campo `variant_id` al modelo `Producto`:

```bash
railway run python manage.py migrate facturacion
```

### 2. Actualizar variant_ids de productos existentes

Para que los webhooks funcionen correctamente con los productos existentes, necesitamos actualizar todos los productos con su correspondiente `variant_id`. Ejecuta el siguiente comando:

```bash
railway run python manage.py actualizar_variant_ids
```

Este comando:
- Consultará la API de Loyverse para cada producto existente
- Obtendrá el `variant_id` correspondiente
- Actualizará el producto en la base de datos
- Mostrará un resumen del proceso

> **Nota**: Este proceso puede tomar varios minutos dependiendo del número de productos. Se procesa en lotes para evitar exceder los límites de la API de Loyverse.

### 3. Verificar configuración de webhooks en Loyverse

Asegúrate de que tienes configurados los siguientes webhooks en la interfaz web de Loyverse:

1. **inventory_levels.update**:
   - URL: `https://backend-production-a8d3.up.railway.app/webhook/`
   - Estado: Habilitado

2. **items.update**:
   - URL: `https://backend-production-a8d3.up.railway.app/webhook/`
   - Estado: Habilitado

Para crear estos webhooks si no existen:
1. Accede a la interfaz web de Loyverse
2. Ve a Configuración > Integraciones > Webhooks
3. Haz clic en "Crear webhook"
4. Selecciona el tipo de evento y configura la URL
5. Guarda la configuración

## Verificación

Para verificar que todo funciona correctamente:

1. Modifica el inventario de un producto en Loyverse (desde la aplicación móvil o web)
2. Verifica en los logs de Railway que se recibe el webhook
3. Comprueba en la base de datos que el producto se ha actualizado correctamente

Ejemplo de consulta para verificar:

```sql
SELECT id, nombre, loyverse_id, variant_id, stock_actual, ultima_actualizacion_stock 
FROM facturacion_producto 
WHERE variant_id IS NOT NULL 
ORDER BY ultima_actualizacion_stock DESC 
LIMIT 10;
```

## Solución de problemas

### Error: Producto no encontrado
Si ves errores de "Producto no encontrado" en los logs, puede ser porque:
1. El producto aún no tiene `variant_id` asignado
2. El webhook está enviando un `variant_id` que no corresponde a ningún producto

Solución: Ejecuta de nuevo `actualizar_variant_ids` para asegurar que todos los productos tienen su `variant_id` correcto.

### Error: Múltiples consultas a la API
Si observas una sobrecarga de peticiones a la API de Loyverse, verifica:
1. Que los productos tienen `variant_id` asignado (para evitar consultas adicionales)
2. Que no hay otros procesos consultando la API innecesariamente

## Mantenimiento continuo

Para mantener sincronizados los `variant_id` cuando se crean nuevos productos, el sistema:

1. Al recibir un webhook `inventory_levels.update`, busca primero por `variant_id`
2. Si no encuentra el producto, busca los detalles del producto mediante la API
3. Actualiza o crea el producto con el `variant_id` correcto

Esto garantiza que nuevos productos añadidos a Loyverse serán correctamente sincronizados. 