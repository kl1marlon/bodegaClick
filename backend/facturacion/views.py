from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, TasaCambio, Factura
from .serializers import (
    ProductoSerializer,
    TasaCambioSerializer,
    FacturaSerializer,
    CrearFacturaSerializer
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
                'message': "Precios sincronizados correctamente"
            })
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)

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