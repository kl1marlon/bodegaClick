from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from facturacion.models import Producto

class ActualizarPreciosBaseAPIView(APIView):
    def post(self, request):
        tasa = request.data.get('tasa')
        if tasa is None:
            return Response({'error': 'Debe indicar la tasa.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tasa = Decimal(tasa)
        except Exception:
            return Response({'error': 'Tasa inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        productos = Producto.objects.all()
        actualizados = 0
        for producto in productos:
            if producto.precio_base_usd and producto.precio_base_usd > 0:
                nuevo_precio = producto.precio_base_usd * tasa
                if producto.precio_base != nuevo_precio:
                    producto.precio_base = nuevo_precio
                    producto.save(update_fields=['precio_base'])
                    actualizados += 1
        return Response({'actualizados': actualizados, 'tasa': str(tasa)}, status=status.HTTP_200_OK)
