from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from facturacion.views import ProductoViewSet, TasaCambioViewSet, FacturaViewSet, WebhookViewSet, WebhookReceiveView
from django.views.generic import RedirectView
from django.http import HttpResponse

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'tasas-cambio', TasaCambioViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'webhooks', WebhookViewSet)

# Vista simple para la página principal
def home_view(request):
    return HttpResponse("""
    <html>
    <head>
        <title>BodegaClick API</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            ul { list-style-type: none; padding: 0; }
            li { margin-bottom: 10px; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .panel { background: #f4f4f4; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-top: 15px; }
        </style>
    </head>
    <body>
        <h1>BodegaClick API</h1>
        <p>La API de BodegaClick está funcionando correctamente.</p>
        
        <div class="panel">
            <h2>Enlaces disponibles:</h2>
            <ul>
                <li><a href="/admin/">Administración</a> - Acceso al panel de administración de Django</li>
                <li><a href="/api/">API</a> - Acceso a los endpoints de la API REST</li>
            </ul>
        </div>
    </body>
    </html>
    """, content_type="text/html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('webhook/', WebhookReceiveView.as_view(), name='webhook-receive'),
    # Añadir la ruta para la URL raíz
    path('', home_view, name='home'),
] 