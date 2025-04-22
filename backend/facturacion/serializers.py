from rest_framework import serializers
from .models import Producto, TasaCambio, Factura, DetalleFactura, Webhook

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
    unidades_paquete = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    aplicarIva = serializers.BooleanField(required=False, default=False)
    precio_base_usd = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    tipo_tasa = serializers.CharField(max_length=10, required=False)
    
    class Meta:
        model = DetalleFactura
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 
                 'precio_compra_usd', 'unidades_paquete', 'total', 'porcentaje_ganancia',
                 'aplicarIva', 'precio_base_usd', 'tipo_tasa']
    
    def validate(self, data):
        from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
        
        # Lista de campos decimales a validar y formatear
        campos_decimales = [
            'cantidad', 'precio_unitario', 'precio_compra_usd', 
            'unidades_paquete', 'porcentaje_ganancia', 'precio_base_usd'
        ]
        
        # Mensaje personalizado por campo
        mensajes_campos = {
            'cantidad': 'La cantidad',
            'precio_unitario': 'El precio unitario',
            'precio_compra_usd': 'El precio de compra',
            'unidades_paquete': 'Las unidades por paquete',
            'porcentaje_ganancia': 'El porcentaje de ganancia',
            'precio_base_usd': 'El precio base USD'
        }
        
        # Validar y formatear cada campo decimal
        for campo in campos_decimales:
            if campo in data:
                try:
                    # Intentar convertir a Decimal si es necesario
                    valor = data[campo]
                    if not isinstance(valor, Decimal):
                        valor = Decimal(str(valor))
                    
                    # Determinar el número de decimales permitidos para el campo
                    decimales = 2
                    
                    # Validar que el número no tenga más decimales de los permitidos
                    decimal_str = str(valor)
                    if '.' in decimal_str:
                        parte_entera, parte_decimal = decimal_str.split('.')
                        if len(parte_decimal) > decimales:
                            nombre_campo = mensajes_campos.get(campo, f'El campo {campo}')
                            raise serializers.ValidationError({
                                campo: f"{nombre_campo} debe tener máximo {decimales} decimales. Valor recibido: {decimal_str}"
                            })
                    
                    # Redondear al número de decimales permitido
                    data[campo] = valor.quantize(Decimal(f'0.{"0" * decimales}'), rounding=ROUND_HALF_UP)
                except InvalidOperation:
                    nombre_campo = mensajes_campos.get(campo, f'El campo {campo}')
                    raise serializers.ValidationError({
                        campo: f"{nombre_campo} debe ser un número decimal válido. Valor recibido: {data[campo]}"
                    })
                except Exception as e:
                    raise serializers.ValidationError({
                        campo: f"Error al procesar el campo {campo}: {str(e)}"
                    })
        
        # Calcular el total automáticamente
        if 'cantidad' in data and 'precio_unitario' in data:
            cantidad = data['cantidad']
            precio = data['precio_unitario']
            data['total'] = (cantidad * precio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
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
            # Extraer datos relevantes para actualizar producto
            producto_obj = detalle_data.get('producto') # Obtenemos el objeto Producto directamente
            cantidad_vendida = detalle_data.get('cantidad')
            precio_compra_usd = detalle_data.get('precio_compra_usd')
            unidades_paquete = detalle_data.get('unidades_paquete')
            precio_base_usd = detalle_data.get('precio_base_usd') # Asumo que quieres actualizar esto también

            # Crear el detalle de factura con todos los campos
            detalle = DetalleFactura.objects.create(factura=factura, **detalle_data)

            # ---- INICIO: Actualizar Producto ----
            if producto_obj:
                try:
                    # No necesitamos buscarlo de nuevo si ya lo tenemos del serializer
                    # Actualizar campos del producto
                    producto_actualizado = False
                    if precio_base_usd is not None and producto_obj.precio_base_usd != precio_base_usd:
                        producto_obj.precio_base_usd = precio_base_usd
                        producto_actualizado = True
                    if precio_compra_usd is not None and producto_obj.precio_compra_usd != precio_compra_usd:
                        producto_obj.precio_compra_usd = precio_compra_usd
                        producto_actualizado = True
                    if unidades_paquete is not None and producto_obj.unidades_paquete != unidades_paquete:
                        producto_obj.unidades_paquete = unidades_paquete
                        producto_actualizado = True
                    
                    # Actualizar stock (restar cantidad vendida)
                    if cantidad_vendida is not None and producto_obj.stock_actual is not None:
                        producto_obj.stock_actual -= cantidad_vendida
                        producto_actualizado = True

                    # Si hubo cambios, actualizar fuente y guardar
                    if producto_actualizado:
                        producto_obj.fuente_actualizacion = 'factura' # Marcar que la factura actualizó
                        producto_obj.save()
                        print(f"Producto ID {producto_obj.id} actualizado por factura.")
                except Producto.DoesNotExist:
                    print(f"Error: Producto con ID {producto_obj.id} no encontrado para actualizar.")
                except Exception as e:
                    print(f"Error al actualizar producto ID {producto_obj.id}: {str(e)}")
            # ---- FIN: Actualizar Producto ----

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

class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ['id', 'merchant_id', 'url', 'type', 'status', 'created_at', 'updated_at']
        read_only_fields = ['merchant_id', 'created_at', 'updated_at']

class CreateWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ['id', 'url', 'type', 'status']
        extra_kwargs = {
            'id': {'required': False},  # Opcional para permitir actualizaciones
            'status': {'required': False}  # Opcional para usar el valor por defecto
        } 