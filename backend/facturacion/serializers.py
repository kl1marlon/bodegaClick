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
    
    class Meta:
        model = DetalleFactura
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'total']

class FacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Factura
        fields = '__all__'

class CrearFacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True)
    
    class Meta:
        model = Factura
        fields = ['moneda', 'tasa_cambio', 'detalles']
    
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        factura = Factura.objects.create(**validated_data)
        
        total_bs = 0
        total_usd = 0
        
        for detalle_data in detalles_data:
            detalle = DetalleFactura.objects.create(factura=factura, **detalle_data)
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