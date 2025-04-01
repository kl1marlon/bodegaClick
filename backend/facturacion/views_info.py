import os
import django
from django.db import connection
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Factura, Producto, TasaCambio

class DatabaseInfoView(APIView):
    """
    Vista para obtener información sobre el estado de la base de datos
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación para diagnóstico
    
    def get(self, request):
        """
        Retorna información sobre el estado de la base de datos y conteos básicos
        """
        try:
            # Verificar conexión a la base de datos
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_connected = cursor.fetchone()[0] == 1
            
            # Contar registros en modelos principales
            facturas_count = Factura.objects.count()
            productos_count = Producto.objects.count()
            tasas_count = TasaCambio.objects.count()
            
            # Obtener información sobre la última factura
            ultima_factura = None
            try:
                factura = Factura.objects.order_by('-fecha').first()
                if factura:
                    ultima_factura = {
                        'id': factura.id,
                        'numero': factura.numero,
                        'fecha': factura.fecha.isoformat(),
                        'total_usd': float(factura.total_usd)
                    }
            except Exception as e:
                ultima_factura = {'error': str(e)}
            
            # Información sobre la base de datos
            db_info = {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default'].get('HOST', 'local'),
                'port': settings.DATABASES['default'].get('PORT', 'default')
            }
            
            return Response({
                'status': 'ok',
                'database': {
                    'connected': db_connected,
                    'info': db_info
                },
                'counts': {
                    'facturas': facturas_count,
                    'productos': productos_count,
                    'tasas_cambio': tasas_count
                },
                'ultima_factura': ultima_factura,
                'django_version': django.__version__,
                'environment': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown')
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500) 