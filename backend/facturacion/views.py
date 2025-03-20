from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, TasaCambio, Factura
from .serializers import (
    ProductoSerializer,
    TasaCambioSerializer,
    FacturaSerializer,
    CrearFacturaSerializer,
    ActualizarPreciosSerializer
)
from .services import LoyverseService

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