from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from facturacion.views import ProductoViewSet, TasaCambioViewSet, FacturaViewSet, WebhookViewSet, WebhookReceiveView, ActualizarVariantIdsView, CrearColumnaVariantIdView, SincronizarInventarioView, SincronizarInventarioHtmlView
from django.http import HttpResponse
import logging
import sys
from django.middleware.common import CommonMiddleware
from django.views.decorators.csrf import csrf_exempt

# Desactivar temporalmente CSRF para el admin
admin.site.login = csrf_exempt(admin.site.login)
admin.site.logout = csrf_exempt(admin.site.logout)

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


# Middleware para silenciar rutas específicas en los logs
class SilentMiddleware(CommonMiddleware):
    """
    Middleware que intercepta las peticiones a ws/notificaciones y las maneja silenciosamente
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.silent_paths = ['/ws/notificaciones']
        
    def __call__(self, request):
        return self.get_response(request)
        
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
    return HttpResponse("<h1>API de Facturación</h1><p>Bienvenido al API de facturación. La documentación está disponible en /api/</p>")

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'tasas-cambio', TasaCambioViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'webhooks', WebhookViewSet)

# Ruta de health check para Railway
def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('', index, name='index'),  # Añadir vista para la ruta raíz
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('webhook/', WebhookReceiveView.as_view(), name='webhook-receive'),
    path('ws/notificaciones/', websocket_dummy_view, name='websocket-dummy'),
    path('api/actualizar-variant-ids/', ActualizarVariantIdsView.as_view(), name='actualizar_variant_ids'),
    path('api/crear-columna-variant-id/', CrearColumnaVariantIdView.as_view(), name='crear_columna_variant_id'),
    path('api/sincronizar-inventario/', SincronizarInventarioView.as_view(), name='sincronizar_inventario'),
    path('sincronizar-inventario/', SincronizarInventarioHtmlView.as_view(), name='sincronizar_inventario_html'),
    path('health/', health_check, name='health_check'),
    
    # Incluir las URLs de facturación para tareas asíncronas
    path('api/', include('facturacion.urls')),
] 