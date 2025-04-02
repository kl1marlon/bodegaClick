# Documentación de BodegaClick

## Endpoints de API y Solución de Problemas CORS

### URL de API

La API principal está alojada en:
```
https://backend-production-a8d3.up.railway.app/api
```

### Endpoints para Facturas

#### Endpoints Originales (Pueden causar timeouts)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/facturas/` | Lista todas las facturas (puede causar timeout) |
| GET | `/api/facturas/{id}/` | Obtiene el detalle de una factura específica |
| POST | `/api/facturas/` | Crea una nueva factura |
| PUT | `/api/facturas/{id}/` | Actualiza una factura existente |
| DELETE | `/api/facturas/{id}/` | Elimina una factura |
| POST | `/api/facturas/{id}/sincronizar/` | Sincroniza una factura con Loyverse |

#### Endpoints Optimizados (Recomendados)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/facturas/listado_simple/` | Lista paginada de facturas optimizada para evitar timeouts |
| GET | `/api/facturas/{id}/detalle_simple/` | Obtiene el detalle optimizado de una factura específica |
| GET | `/api/facturas/buscar-por-producto/{id}/` | Busca todas las facturas que contienen un producto específico |

#### Parámetros para Endpoints Optimizados

Para `/api/facturas/listado_simple/`:
- `page`: Número de página (default: 1)
- `page_size`: Tamaño de página (default: 20, máximo: 100)

Ejemplo:
```
/api/facturas/listado_simple/?page=2&page_size=50
```

### Implementación en el Frontend

#### Archivos Modificados

1. **facturasSlice.js**
   - Ubicación: `frontend/src/store/facturasSlice.js`
   - Contiene la lógica para interactuar con la API de facturas
   - Incluye funciones optimizadas para evitar problemas de timeout

2. **ListaDeFacturas.js**
   - Ubicación: `frontend/src/pages/ListaDeFacturas.js`
   - Componente React que muestra la lista de facturas
   - Utiliza los endpoints optimizados para mejorar el rendimiento

3. **BusquedaProductoHistorial.js** (Nuevo)
   - Ubicación: `frontend/src/pages/BusquedaProductoHistorial.js`
   - Componente para buscar un producto y ver su historial de compras
   - Muestra cuándo fue la última vez que se compró un producto específico

#### Funciones Principales en facturasSlice.js

| Función | Descripción |
|---------|-------------|
| `fetchFacturasOptimizado` | Obtiene la lista paginada de facturas usando el endpoint optimizado |
| `fetchFacturaDetalleOptimizado` | Obtiene el detalle de una factura específica usando el endpoint optimizado |
| `setPage` | Cambia la página actual en la paginación |
| `setPageSize` | Cambia el tamaño de página en la paginación |

### Configuración CORS en el Backend

La configuración CORS se encuentra en:
```
backend/config/settings.py
```

Se han añadido los siguientes encabezados a la lista de encabezados permitidos:
- `cache-control`
- `pragma`

Esto permite que el frontend pueda enviar estos encabezados en sus solicitudes sin ser bloqueado por la política CORS.

### Solución de Problemas

#### Problema de Timeout

Si experimentas timeouts al cargar facturas, asegúrate de:
1. Usar los endpoints optimizados (`/api/facturas/listado_simple/`)
2. Implementar paginación para reducir la cantidad de datos cargados a la vez
3. Aumentar el timeout en las solicitudes axios si es necesario

#### Problema de CORS

Si experimentas errores CORS:
1. Verifica que los encabezados necesarios estén incluidos en `CORS_ALLOW_HEADERS` en `settings.py`
2. Asegúrate de que el dominio del frontend esté incluido en `CORS_ALLOWED_ORIGINS`
3. Considera eliminar temporalmente los encabezados problemáticos en las solicitudes del frontend

### Mejoras Implementadas

1. **Paginación del lado del servidor**
   - Reduce la carga en el servidor y mejora el rendimiento
   - Permite manejar grandes cantidades de facturas sin problemas

2. **Optimización de consultas**
   - Selección optimizada de datos relacionados
   - Conversión explícita de valores numéricos para evitar problemas de serialización

3. **Manejo mejorado de errores**
   - Mensajes de error más detallados
   - Mejor experiencia de usuario cuando ocurren errores

4. **Búsqueda de productos en historial de facturas**
   - Nueva interfaz para buscar productos y ver cuándo fueron comprados por última vez
   - Facilita el análisis de compras históricas de productos específicos

### Próximos Pasos Recomendados

1. **Monitoreo de rendimiento**
   - Verificar si los nuevos endpoints resuelven los problemas de timeout
   - Identificar posibles cuellos de botella adicionales

2. **Optimización adicional**
   - Considerar la implementación de caché para consultas frecuentes
   - Optimizar las consultas a la base de datos con índices adicionales

3. **Mejoras en la interfaz de usuario**
   - Añadir más opciones de filtrado para facilitar la búsqueda de facturas
   - Mejorar la visualización de estadísticas y datos agregados

4. **Implementar backend para búsqueda de productos**
   - Crear el endpoint `GET /api/facturas/buscar-por-producto/{id}/` en el backend
   - Optimizar la consulta para manejar grandes cantidades de facturas
   - Incluir información relevante sobre cada aparición del producto en las facturas

### Implementación del Endpoint de Búsqueda de Productos en Facturas

Para implementar el nuevo endpoint de búsqueda de productos en el historial de facturas, se debe agregar lo siguiente al backend:

1. **Añadir nueva acción al ViewSet de Facturas**:

```python
@action(detail=False, methods=['get'], url_path='buscar-por-producto/(?P<producto_id>[^/.]+)')
def buscar_por_producto(self, request, producto_id=None):
    """
    Endpoint para buscar todas las facturas que contienen un producto específico.
    Devuelve un listado de apariciones del producto en diferentes facturas.
    """
    try:
        # Verificar que el producto existe
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"error": f"No se encontró el producto con ID {producto_id}"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Buscar todas las apariciones del producto en detalles de facturas
        detalles = DetalleFactura.objects.filter(
            producto_id=producto_id
        ).select_related('factura').order_by('-factura__fecha')
        
        # Preparar respuesta
        resultados = []
        for detalle in detalles:
            resultados.append({
                'id': detalle.id,
                'factura_id': detalle.factura.id,
                'numero': detalle.factura.numero,
                'fecha': detalle.factura.fecha,
                'cantidad': float(detalle.cantidad),
                'precio_unitario': float(detalle.precio_unitario),
                'total': float(detalle.total),
                'moneda': detalle.factura.moneda
            })
            
        return Response(resultados)
        
    except Exception as e:
        import traceback
        print(f"Error al buscar por producto: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {"error": f"Error al buscar facturas por producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

Este endpoint se puede llamar desde el frontend usando la URL `/api/facturas/buscar-por-producto/{id}/` y devolverá un listado de todas las apariciones del producto en las diferentes facturas, ordenadas por fecha de factura descendente (más reciente primero).
