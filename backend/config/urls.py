from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from facturacion.views import ProductoViewSet, TasaCambioViewSet, FacturaViewSet, WebhookViewSet, WebhookReceiveView
from django.http import HttpResponse
import logging
import sys
from django.middleware.common import CommonMiddleware

# Suprimir completamente los logs para ws/notificaciones
class NoWSLoggingFilter(logging.Filter):
    def filter(self, record):
        return 'ws/notificaciones' not in record.getMessage()

# Aplicar el filtro al logger raíz
root_logger = logging.getLogger()
root_logger.addFilter(NoWSLoggingFilter())

# También aplicar al logger de Django
django_logger = logging.getLogger('django')
django_logger.addFilter(NoWSLoggingFilter())

# Y al logger de django.server (que maneja las solicitudes HTTP)
server_logger = logging.getLogger('django.server')
server_logger.addFilter(NoWSLoggingFilter())

# Clase para silenciar stdout/stderr durante la solicitud
class SilenceOutput:
    def __init__(self):
        self.original_stdout = None
        self.original_stderr = None
        self.null_output = open('/dev/null', 'w')

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.null_output
        sys.stderr = self.null_output

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.null_output.close()


class SilentMiddleware(CommonMiddleware):
    """
    Middleware que intercepta las peticiones a ws/notificaciones y las maneja silenciosamente
    """
    def process_request(self, request):
        if request.path.startswith('/ws/notificaciones/'):
            return None
        return super().process_request(request)

def websocket_dummy_view(request):
    """
    Vista simple que responde a las peticiones WebSocket con un 200 OK
    para evitar errores 404 en los logs
    """
    return HttpResponse(status=200)

# Vista simple para la ruta raíz
def index(request):
    return HttpResponse("Backend BodegaClick funcionando correctamente", content_type="text/plain")

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'tasas-cambio', TasaCambioViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'webhooks', WebhookViewSet)

urlpatterns = [
    path('', index, name='index'),  # Añadir vista para la ruta raíz
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('webhook/', WebhookReceiveView.as_view(), name='webhook-receive'),
    path('ws/notificaciones/', websocket_dummy_view, name='websocket-dummy'),
] 