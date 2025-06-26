# Sistema de Facturación

## Descripción General

El Sistema de Facturación de BodegaClick proporciona una plataforma completa para la gestión de facturas, permitiendo registrar ventas en múltiples monedas (USD y Bolívares) y sincronizar esta información con el sistema de punto de venta Loyverse. Este documento describe la arquitectura, componentes y flujos de trabajo del sistema de facturación.

## Estructura de Datos

### Modelos Principales

#### Factura

El modelo `Factura` representa el documento principal de una transacción comercial:

```python
class Factura(models.Model):
    MONEDA_CHOICES = [
        ('USD', 'Dólares'),
        ('BS', 'Bolívares'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES)
    tasa_cambio = models.ForeignKey(TasaCambio, on_delete=models.PROTECT, null=True, blank=True)
    total_bs = models.DecimalField(max_digits=15, decimal_places=2)
    total_usd = models.DecimalField(max_digits=15, decimal_places=2)
    sincronizado_loyverse = models.BooleanField(default=False)
    porcentaje_ganancia = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
```

**Características importantes:**
- Soporte para dos monedas (USD y Bolívares)
- Referencia a la tasa de cambio utilizada en el momento de la transacción
- Campos para totales en ambas monedas
- Control de sincronización con Loyverse
- Porcentaje de ganancia aplicado a la factura completa

#### DetalleFactura

El modelo `DetalleFactura` representa cada línea o ítem de una factura:

```python
class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje_ganancia = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precio_compra_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unidades_paquete = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    aplicarIva = models.BooleanField(default=False)
    precio_base_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_tasa = models.CharField(max_length=10, null=True, blank=True)
```

**Características importantes:**
- Relación con la factura principal y el producto vendido
- Información detallada de cantidad y precios
- Capacidad para establecer porcentajes de ganancia específicos por producto
- Control de IVA por línea de factura
- Información sobre precio de compra en USD y unidades por paquete para cálculos de rentabilidad
- Tipo de tasa utilizada para la conversión (BCV o PARALELO)

## Procesos de Facturación

### Flujo de Creación de Factura

1. **Iniciación**: Se recibe una solicitud para crear una nueva factura con información básica (moneda, tasa de cambio) y detalles de productos.
2. **Validación de Datos**: Se validan los datos recibidos, asegurando que los campos numéricos cumplan con las restricciones (máximo 2 decimales).
3. **Cálculo de Totales**: Para cada detalle de la factura:
   - Si la moneda es BS: El precio_compra_usd representa montos en bolívares.
   - Si la moneda es USD: El precio_compra_usd representa montos en dólares.
4. **Conversión Monetaria**: Se realizan conversiones entre USD y BS según la tasa de cambio referenciada.
5. **Almacenamiento**: Se guarda la factura con todos sus detalles.
6. **Actualización de Inventario**: Se actualizan los niveles de inventario de los productos vendidos.

### Recálculo de Totales

El sistema implementa un proceso específico para recalcular los totales de las facturas mediante el script `recalcular_totales_facturas.py`:

```python
def recalcular_totales(factura):
    try:
        total_bs = Decimal('0')
        total_usd = Decimal('0')
        
        # Usar la tasa de cambio asociada a la factura
        if factura['tasa_valor'] is None:
            tasa_cambio = Decimal('1')
        else:
            tasa_cambio = Decimal(str(factura['tasa_valor']))
        
        # Sumar los precio_compra_usd de todos los detalles
        suma_detalles = Decimal('0')
        for detalle in factura['detalles']:
            if detalle['precio_compra_usd'] is not None:
                suma_detalles += Decimal(str(detalle['precio_compra_usd']))
        
        # Aplicar lógica según moneda
        if factura['moneda'] == 'BS':
            total_bs = suma_detalles
            total_usd = total_bs / tasa_cambio if tasa_cambio != Decimal('0') else Decimal('0')
        else:  # USD
            total_usd = suma_detalles
            total_bs = total_usd * tasa_cambio
        
        return {
            'total_bs': total_bs.quantize(Decimal('0.01')),
            'total_usd': total_usd.quantize(Decimal('0.01'))
        }
    except Exception as e:
        # En caso de error, mantener los totales originales
        return {
            'total_bs': Decimal(str(factura['total_bs'])).quantize(Decimal('0.01')),
            'total_usd': Decimal(str(factura['total_usd'])).quantize(Decimal('0.01'))
        }
```

## Integración con Loyverse

### Sincronización de Facturas

La clase `LoyverseService` proporciona métodos para sincronizar información de facturas con Loyverse:

1. **Actualización de Precios**: Los precios calculados en facturas pueden sincronizarse con Loyverse.
2. **Recepción de Actualizaciones**: El sistema recibe actualizaciones desde Loyverse a través de webhooks.

### Webhooks

El sistema incluye gestión de webhooks para recibir notificaciones desde Loyverse:

```python
class WebhookReceiveView(APIView):
    # Endpoint para recibir notificaciones desde Loyverse
    def post(self, request):
        # Verificar firma
        # Procesar actualización de inventario o productos
        # Retornar respuesta
```

## Cálculo de Precios y Rentabilidad

### Lógica de Cálculo de Precios de Venta

El sistema permite calcular precios de venta basados en costos, porcentajes de ganancia y tasas de cambio:

```python
def calcular_precios_venta(self, producto_id=None, porcentaje_ganancia=None):
    # Obtener la última tasa paralelo
    tasa_paralelo = TasaCambio.objects.filter(tipo='PARALELO').latest('fecha')
    
    # Filtrar productos
    if producto_id:
        productos = Producto.objects.filter(id=producto_id)
    else:
        productos = Producto.objects.all()
        
    # Para cada producto calcular el precio de venta
    for producto in productos:
        if producto.precio_compra_usd > 0 and producto.unidades_paquete > 0:
            porcentaje = porcentaje_ganancia if porcentaje_ganancia is not None else Decimal('30.0')
            
            # Cálculo del precio base y precio de venta
            precio_base = (producto.precio_compra_usd * tasa_paralelo.valor) / Decimal(producto.unidades_paquete)
            precio_venta = precio_base * (Decimal('1.0') + (porcentaje / Decimal('100.0')))
            
            # Aplicar reglas de redondeo especiales para precios en bolívares
            precio_final = aplicar_redondeo_especial(precio_venta)
            
            # Actualizar producto
            producto.precio_venta_calculado = precio_final
            producto.precio_base = precio_final
            producto.save()
```

### Actualización de Precios desde Facturas

El sistema puede actualizar los precios de los productos basándose en las facturas registradas:

```python
def actualizar_precios_desde_factura(self, factura_id):
    # Obtener factura y sus detalles
    # Para cada detalle, actualizar precios en el producto correspondiente
    # Sincronizar con Loyverse si es necesario
```

## API Endpoints

El sistema expone varios endpoints para manejar las operaciones de facturación:

### FacturaViewSet

```python
class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all().order_by('-fecha')
    
    # Diferentes serializers según la acción
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearFacturaSerializer
        return FacturaSerializer
```

**Endpoints principales**:
- `GET /facturas/`: Lista todas las facturas
- `POST /facturas/`: Crea una nueva factura
- `GET /facturas/{id}/`: Obtiene detalle de una factura específica

## Seguridad y Validación

### Validación de Datos

El sistema implementa validaciones rigurosas para los datos de facturación:

1. **Validación de decimales**: Control estricto para campos numéricos (máximo 2 decimales)
2. **Validación de requisitos**: Campos obligatorios para la creación de facturas
3. **Manejo personalizado de errores**: Mensajes de error descriptivos para campos con problemas específicos

### Protección de Datos

1. **Protección contra eliminación**: Se utiliza `on_delete=models.PROTECT` para evitar la eliminación de productos referenciados en facturas.
2. **Auditoría**: Se registra la fecha de creación y actualización para facilitar auditorías.

## Buenas Prácticas y Extensibilidad

### Buenas Prácticas

1. **Separación de responsabilidades**:
   - Los modelos (`models.py`) definen la estructura de datos
   - Los servicios (`services.py`) manejan la lógica de negocio
   - Las vistas (`views.py`) gestionan las solicitudes HTTP

2. **Manejo de errores robusto**: Todos los procesos incluyen manejo de excepciones y registro detallado de logs.

3. **Transacciones atómicas**: Las operaciones críticas utilizan transacciones para mantener la integridad de los datos.

### Extensibilidad

El sistema de facturación está diseñado para ser fácilmente extensible:

1. **Nuevos tipos de factura**: La estructura permite agregar nuevos tipos o estados de factura.
2. **Integración con otros sistemas**: La arquitectura basada en servicios facilita la integración con sistemas adicionales.
3. **Personalización de cálculos**: La lógica de cálculo de precios y totales puede ser modificada sin afectar el resto del sistema.

## Casos de Uso Comunes

1. **Crear una nueva factura con múltiples productos**
2. **Recalcular totales de facturas después de cambios en tasas de cambio**
3. **Obtener reportes de ventas en diferentes monedas**
4. **Sincronizar precios calculados desde facturas hacia Loyverse**
5. **Ajustar porcentajes de ganancia para productos específicos**

## Solución de Problemas

### Problemas Comunes

1. **Discrepancias en totales**: Ejecutar el script de recálculo de totales (`recalcular_totales_facturas.py`)
2. **Errores de sincronización con Loyverse**: Verificar la configuración del token API y la conexión a Internet
3. **Problemas de conversión monetaria**: Asegurar que existen tasas de cambio actualizadas en el sistema

### Recomendaciones

- Mantener actualizadas las tasas de cambio antes de crear nuevas facturas
- Verificar la consistencia de los datos de unidades por paquete para cálculos precisos
- Realizar copias de seguridad periódicas de la base de datos, especialmente antes de ejecutar scripts de actualización masiva
