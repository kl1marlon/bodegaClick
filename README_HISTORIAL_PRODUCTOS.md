# Historial de Compras de Productos en BodegaClick

## Descripción de la Funcionalidad

Esta nueva funcionalidad permite a los usuarios buscar un producto específico y ver el historial completo de sus compras, incluyendo:
- Cuándo fue la última vez que se compró
- A qué precio se compró en cada ocasión 
- La cantidad comprada
- Información detallada de las facturas asociadas

## Implementación Técnica

### 1. Backend (Django + DRF)

Se implementó un nuevo endpoint en el backend para buscar productos en el historial de facturas:

```python
@action(detail=False, methods=['get'], url_path='buscar-por-producto/(?P<producto_id>[^/.]+)')
def buscar_por_producto(self, request, producto_id=None):
    """
    Endpoint para buscar todas las facturas que contienen un producto específico.
    Devuelve un listado de apariciones del producto en diferentes facturas.
    """
    # [Código de implementación]
```

Este endpoint devuelve un objeto JSON con:
- `resumen`: Información resumida del producto y sus compras
- `compras`: Lista detallada de todas las compras, ordenadas por fecha descendente

#### Estructura de Respuesta

```json
{
  "resumen": {
    "nombre_producto": "Producto Ejemplo",
    "categoria": "Categoría Ejemplo",
    "total_compras": 5,
    "ultima_compra": "2023-06-15",
    "precio_promedio_usd": 12.5,
    "cantidad_total": 25
  },
  "compras": [
    {
      "id": 123,
      "factura_id": 45,
      "numero": "F20230615-1234",
      "fecha": "2023-06-15",
      "cantidad": 5,
      "precio_unitario": 12.5,
      "precio_unitario_usd": 12.5,
      "precio_unitario_bs": 375.0,
      "total": 62.5,
      "moneda": "USD",
      "tasa_cambio": {
        "id": 89,
        "tipo": "PARALELO",
        "valor": 30.0,
        "fecha": "2023-06-15"
      },
      "unidades_paquete": 1.0,
      "aplicar_iva": false,
      "sincronizado": true
    },
    // ... más compras
  ]
}
```

### 2. Frontend (React + MUI)

Se crearon los siguientes componentes y archivos:

#### 2.1. `BusquedaProductoHistorial.js`

Página principal que permite:
- Buscar productos usando el componente `BuscadorProductos` existente
- Mostrar información detallada del producto seleccionado
- Visualizar un resumen de la última compra
- Mostrar una tabla con el historial completo de compras

#### 2.2. Modificaciones en el enrutamiento

Se agregó una nueva ruta en `App.js`:
```jsx
<Route path="/buscar-producto-historial" element={<BusquedaProductoHistorial />} />
```

#### 2.3. Integración en el menú

Se agregó un enlace en el menú de navegación lateral (`Layout.js`):
```jsx
{ text: 'Buscar Producto', icon: <SearchIcon />, path: '/buscar-producto-historial' }
```

#### 2.4. Acceso rápido desde la lista de facturas

Se agregó un botón en `ListaDeFacturas.js` para acceso rápido a la nueva funcionalidad:
```jsx
<Button
  variant="outlined"
  color="info"
  onClick={() => navigate('/buscar-producto-historial')}
  sx={{ mr: 1 }}
>
  Buscar Producto
</Button>
```

## Flujo de Uso

1. El usuario accede a la página "Buscar Producto" desde:
   - El menú lateral
   - El botón en la lista de facturas

2. Busca y selecciona un producto específico usando el buscador

3. El sistema muestra:
   - Información básica del producto
   - Estadísticas de compra (número total, precio promedio, etc.)
   - Una tarjeta destacada con la compra más reciente
   - Una tabla con el historial completo de compras

4. El usuario puede:
   - Ver los detalles completos de cada compra
   - Acceder directamente a las facturas relacionadas

## Ventajas de la Funcionalidad

- **Trazabilidad de productos**: Facilita conocer cuándo y a qué precio se adquirió cada producto
- **Análisis de costos**: Permite ver la evolución de precios de los productos en el tiempo
- **Toma de decisiones**: Ayuda a decidir cuándo realizar nuevas compras basándose en datos históricos
- **Búsqueda eficiente**: Evita tener que revisar facturas individuales para encontrar un producto específico

## Tecnologías Utilizadas

- **Backend**: Django, Django REST Framework
- **Frontend**: React, Material UI
- **Comunicación**: API RESTful, Axios
- **Manejo de estado**: Redux (para productos)
- **Formateo de fechas**: Moment.js

## Posibles Mejoras Futuras

1. **Gráficos de evolución de precios**: Implementar visualizaciones gráficas de la evolución de precios a lo largo del tiempo
2. **Filtros adicionales**: Permitir filtrar el historial por rango de fechas, proveedores, etc.
3. **Exportación de datos**: Añadir opciones para exportar el historial en formatos como CSV o Excel
4. **Notificaciones**: Implementar alertas para productos que no se han comprado en un tiempo determinado
5. **Sugerencias de compra**: Integrar con un sistema de sugerencias basado en patrones históricos de compra 