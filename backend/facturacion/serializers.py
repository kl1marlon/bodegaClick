from rest_framework import serializers
from .models import Producto, TasaCambio, Factura, DetalleFactura

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class TasaCambioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TasaCambio
        fields = '__all__'

class DetalleFacturaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_compra_usd = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = DetalleFactura
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 
                 'precio_compra_usd', 'unidades_paquete', 'total', 'porcentaje_ganancia']
    
    def validate(self, data):
        # Calcular el total automáticamente
        if 'cantidad' in data and 'precio_unitario' in data:
            from decimal import Decimal, ROUND_HALF_UP
            # Calcular y redondear el total a 2 decimales
            cantidad = Decimal(str(data['cantidad']))
            precio = Decimal(str(data['precio_unitario']))
            data['total'] = (cantidad * precio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        # Asegurarse de que todos los valores decimales estén redondeados a 2 decimales
        if 'precio_compra_usd' in data:
            from decimal import Decimal, ROUND_HALF_UP
            data['precio_compra_usd'] = Decimal(str(data['precio_compra_usd'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        return data

class FacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Factura
        fields = '__all__'

class CrearFacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True)
    
    class Meta:
        model = Factura
        fields = ['moneda', 'tasa_cambio', 'porcentaje_ganancia', 'detalles']
    
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        # Generar un número de factura único
        import random
        import datetime
        now = datetime.datetime.now()
        numero_factura = f"F{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # Inicializar la factura con totales en cero
        factura = Factura.objects.create(
            numero=numero_factura,
            total_bs=0,
            total_usd=0,
            **validated_data
        )
        
        total_bs = 0
        total_usd = 0
        
        for detalle_data in detalles_data:
            # También guardamos el precio de compra y las unidades para actualizar el producto después
            precio_compra_usd = detalle_data.get('precio_compra_usd')
            unidades_paquete = detalle_data.get('unidades_paquete')
            
            # Crear el detalle de factura con todos los campos
            detalle = DetalleFactura.objects.create(factura=factura, **detalle_data)
            
            # Actualizar totales
            if factura.moneda == 'BS':
                total_bs += detalle.total
                total_usd = total_bs / factura.tasa_cambio.valor if factura.tasa_cambio else 0
            else:
                total_usd += detalle.total
                total_bs = total_usd * factura.tasa_cambio.valor if factura.tasa_cambio else 0
        
        factura.total_bs = total_bs
        factura.total_usd = total_usd
        factura.save()
        
        return factura

class ActualizarPreciosSerializer(serializers.Serializer):
    factura_id = serializers.IntegerField(required=False, help_text="ID de la factura para procesar")
    producto_id = serializers.IntegerField(required=False, help_text="ID del producto para actualizar precio")
    porcentaje_ganancia = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, 
                                                 help_text="Porcentaje de ganancia a aplicar")
    
    def validate(self, data):
        # Verificar que al menos se proporcione un id de factura o producto
        if 'factura_id' not in data and 'producto_id' not in data:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un ID de factura o un ID de producto"
            )
        return data 