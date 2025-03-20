from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Producto, TasaCambio, Factura, Webhook
from .serializers import (
    ProductoSerializer,
    TasaCambioSerializer,
    FacturaSerializer,
    CrearFacturaSerializer,
    ActualizarPreciosSerializer,
    WebhookSerializer,
    CreateWebhookSerializer
)
from .services import LoyverseService
import json
import hmac
import hashlib
import base64
import uuid
from django.conf import settings
import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    
    @action(detail=False, methods=['post'])
    def sync_from_loyverse(self, request):
        service = LoyverseService()
        result = service.fetch_products()
        
        if result['success']:
            return Response({
                'message': f"Productos sincronizados. Creados: {result['created']}, Actualizados: {result['updated']}"
            })
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def sync_to_loyverse(self, request):
        service = LoyverseService()
        products = Producto.objects.all()
        result = service.sync_prices(products)
        
        if result['success']:
            return Response({
                'message': f"Precios sincronizados correctamente. Actualizados: {result['updated']}"
            })
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def calcular_precios(self, request):
        serializer = ActualizarPreciosSerializer(data=request.data)
        if serializer.is_valid():
            service = LoyverseService()
            
            # Si se proporciona ID de factura, procesar desde factura
            if 'factura_id' in serializer.validated_data:
                result = service.actualizar_precios_desde_factura(
                    serializer.validated_data['factura_id']
                )
            else:
                # Procesar un producto específico o todos si no se especifica
                producto_id = serializer.validated_data.get('producto_id')
                porcentaje = serializer.validated_data.get('porcentaje_ganancia')
                
                result = service.calcular_precios_venta(producto_id, porcentaje)
                
                # Si el cálculo fue exitoso, sincronizar con Loyverse
                if result['success'] and producto_id:
                    producto = Producto.objects.get(id=producto_id)
                    service.sync_prices([producto])
            
            if result['success']:
                return Response(result)
            
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TasaCambioViewSet(viewsets.ModelViewSet):
    queryset = TasaCambio.objects.all().order_by('-fecha')
    serializer_class = TasaCambioSerializer
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        tipo = request.query_params.get('tipo', 'BCV')
        try:
            tasa = TasaCambio.objects.filter(tipo=tipo).latest('fecha')
            serializer = self.get_serializer(tasa)
            return Response(serializer.data)
        except TasaCambio.DoesNotExist:
            return Response({
                'error': f'No hay tasa de cambio {tipo} registrada'
            }, status=status.HTTP_404_NOT_FOUND)

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all().order_by('-fecha')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearFacturaSerializer
        return FacturaSerializer
    
    def create(self, request, *args, **kwargs):
        print("Datos recibidos:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Errores de validación:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = serializer.save()
            return Response(FacturaSerializer(instance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Error al crear factura:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def procesar_factura(self, request, pk=None):
        """
        Procesa una factura existente para actualizar precios y sincronizar con Loyverse
        """
        service = LoyverseService()
        result = service.actualizar_precios_desde_factura(pk)
        
        if result['success']:
            return Response({
                'message': f"Factura procesada correctamente. Productos actualizados: {result['productos_actualizados']}",
                'detalle': result
            })
        
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)

class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateWebhookSerializer
        return WebhookSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Generar UUID si no se proporciona
            if not serializer.validated_data.get('id'):
                serializer.validated_data['id'] = str(uuid.uuid4())
            
            # Agregar el merchant_id (asumiendo que está en configuración o se obtiene de alguna manera)
            webhook = serializer.save(merchant_id=settings.LOYVERSE_MERCHANT_ID)
            
            return Response(
                WebhookSerializer(webhook).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Envía una solicitud de prueba al webhook
        """
        webhook = self.get_object()
        service = LoyverseService()
        result = service.test_webhook(webhook)
        
        if result['success']:
            return Response({
                'message': 'Webhook probado correctamente',
                'details': result
            })
        
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)

class WebhookReceiveView(APIView):
    def post(self, request):
        """
        Endpoint para recibir notificaciones de webhook desde Loyverse
        """
        # Verificar firma del webhook para validar autenticidad
        signature = request.headers.get('X-Loyverse-Signature')
        if not self._verify_signature(request.body, signature):
            return Response({'error': 'Firma inválida'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = json.loads(request.body)
            event_type = data.get('type')
            
            # Manejar el evento según su tipo
            if event_type == 'inventory_levels.update':
                self._handle_inventory_update(data)
            # Otros tipos se pueden manejar aquí
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _verify_signature(self, payload, signature):
        """
        Verifica la firma del webhook usando HMAC con SHA-256
        """
        if not signature or not settings.LOYVERSE_WEBHOOK_SECRET:
            return False
        
        # Calcular firma esperada
        expected = base64.b64encode(
            hmac.new(
                settings.LOYVERSE_WEBHOOK_SECRET.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Comparar con la firma recibida
        return hmac.compare_digest(expected, signature)
    
    def _handle_inventory_update(self, data):
        """
        Maneja la actualización de inventario
        """
        channel_layer = get_channel_layer()
        inventory_levels = data.get('inventory_levels', [])
        service = LoyverseService()
        
        for level in inventory_levels:
            variant_id = level.get('variant_id')
            store_id = level.get('store_id')
            in_stock = level.get('in_stock')
            
            # Buscar el producto correspondiente
            try:
                producto = Producto.objects.get(loyverse_id=variant_id)
                
                # Guardar el stock anterior para comparar
                stock_anterior = producto.stock_actual
                
                # Actualizar el stock del producto
                producto.stock_actual = in_stock
                producto.ultima_actualizacion_stock = datetime.datetime.now()
                producto.save()
                
                print(f"Inventario actualizado para {producto.nombre}: {in_stock} unidades")
                
                # Enviar notificación en tiempo real
                async_to_sync(channel_layer.group_send)(
                    "inventario_updates",
                    {
                        'type': 'inventory_update',
                        'producto': {
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'loyverse_id': producto.loyverse_id
                        },
                        'stock_actual': float(in_stock),
                        'stock_anterior': float(stock_anterior),
                        'message': f"El inventario de {producto.nombre} ha cambiado de {stock_anterior} a {in_stock} unidades"
                    }
                )
                
            except Producto.DoesNotExist:
                # Si el producto no existe, sincronizar desde Loyverse
                print(f"Producto con ID {variant_id} no encontrado. Sincronizando productos...")
                service.fetch_products() 