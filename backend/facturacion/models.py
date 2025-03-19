from django.db import models

class Producto(models.Model):
    loyverse_id = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return f"Factura #{self.numero}"

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} x {self.precio_unitario}" 