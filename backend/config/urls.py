from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from facturacion.views import ProductoViewSet, TasaCambioViewSet, FacturaViewSet, WebhookViewSet, WebhookReceiveView

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'tasas-cambio', TasaCambioViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'webhooks', WebhookViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('webhook/', WebhookReceiveView.as_view(), name='webhook-receive'),
] 