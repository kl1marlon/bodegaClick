from django.db import models

class Producto(models.Model):
    loyverse_id = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidades_compra = models.IntegerField(default=1)
    precio_compra_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidades_paquete = models.IntegerField(default=1)
    precio_venta_calculado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion_precio = models.DateTimeField(null=True, blank=True)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion_stock = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categoria = models.CharField(max_length=255, null=True, blank=True)
    fuente_actualizacion = models.CharField(max_length=50, default='loyverse', blank=True, help_text="Indica la fuente de la última actualización (loyverse, factura)")

    def __str__(self):
        return self.nombre

class TasaCambio(models.Model):
    TIPO_CHOICES = [
        ('BCV', 'Tasa BCV'),
        ('PARALELO', 'Tasa Paralelo'),
    ]
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.valor} - {self.fecha.strftime('%Y-%m-%d')}"

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

    def __str__(self):
        return f"Factura #{self.numero}"

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje_ganancia = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precio_compra_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unidades_paquete = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} x {self.precio_unitario}"

class Webhook(models.Model):
    TYPE_CHOICES = [
        ('inventory_levels.update', 'Actualización de niveles de inventario'),
        ('items.update', 'Actualización de items'),
        ('customers.update', 'Actualización de clientes'),
        ('receipts.update', 'Actualización de recibos'),
        ('shifts.create', 'Creación de turnos'),
    ]
    
    STATUS_CHOICES = [
        ('ENABLED', 'Habilitado'),
        ('DISABLED', 'Deshabilitado'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36)  # UUID
    merchant_id = models.CharField(max_length=36)
    url = models.URLField()
    type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ENABLED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.type} - {self.url}" 